"""A patch-embedding vision prefix fused into mission 01's decoder.

[`02-pretrain/core/model.py`](../../../01-language-model-agent/02-pretrain/core/model.py)
hardcodes exactly one input path (`nn.Embedding(vocab_size, d_model)`, causal
attention only). This file imports the pieces of that model that are already
architecture-agnostic -- `RMSNorm`, `SwiGLU`, and the RoPE cache/apply
functions -- unmodified, and builds the two pieces that file does not have:
a patch embedding that turns a 32x32 image into a short sequence of vision
tokens, and an attention variant that accepts an explicit additive mask
instead of a hardcoded `is_causal=True`, so the same class serves as a plain
causal decoder (`use_vision=False`, the text-only baseline) or a
vision-prefixed one (`use_vision=True`) depending on one constructor flag,
without duplicating the causal path twice.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[3]
        / "01-language-model-agent"
        / "02-pretrain"
        / "core"
    ),
)
from model import RMSNorm, SwiGLU, apply_rope, build_rope_cache

IGNORE_INDEX = -100  # matches mission 01 stage 03's masked-loss convention

IMG_SIZE = 32
PATCH = 4
PATCHES_PER_SIDE = IMG_SIZE // PATCH  # 8
NUM_VISION_TOKENS = PATCHES_PER_SIDE * PATCHES_PER_SIDE  # 64
PATCH_DIM = PATCH * PATCH * 3  # 48
NEG = -1e9  # additive-mask "disallowed"; finite so a fully-vision-attending
# row never produces an all -inf softmax input


@dataclass
class Config:
    vocab_size: int
    d_model: int = 128
    n_layer: int = 4
    n_head: int = 4
    n_kv_head: int = 2
    d_ff: int = 336  # ~2/3 * 4 * d_model, the SwiGLU convention mission 01 uses
    rope_theta: float = 10_000.0

    @property
    def d_head(self) -> int:
        return self.d_model // self.n_head


class VisionPatchEmbed(nn.Module):
    """32x32 RGB image -> 64 patch tokens of d_model each.

    Pixels are normalized from [0, 255] to roughly [-1, 1] (zero-centered, the
    convention most vision encoders use so the first linear layer sees a
    signed input rather than an all-positive one). Patches have no sequential
    order among themselves, so position is a small learned lookup table, not
    RoPE -- RoPE encodes a *difference* between two positions in a sequence,
    which is the wrong tool for an unordered 8x8 grid.
    """

    def __init__(self, cfg: Config):
        super().__init__()
        self.proj = nn.Linear(PATCH_DIM, cfg.d_model)
        self.pos = nn.Embedding(NUM_VISION_TOKENS, cfg.d_model)

    def forward(self, pixels: torch.Tensor) -> torch.Tensor:
        # pixels: (B, 1024, 3) float, row-major 32x32 RGB in [0, 255].
        B = pixels.shape[0]
        grid = pixels.view(B, IMG_SIZE, IMG_SIZE, 3)
        patches = grid.unfold(1, PATCH, PATCH).unfold(2, PATCH, PATCH)
        # -> (B, 8, 8, 3, 4, 4); reorder to (B, 8, 8, 4, 4, 3) so each patch's
        # last 48 values are (row, col, channel) in a fixed, consistent order.
        patches = patches.permute(0, 1, 2, 4, 5, 3).contiguous()
        patches = patches.view(B, NUM_VISION_TOKENS, PATCH_DIM)
        patches = (patches / 127.5) - 1.0
        tokens = self.proj(patches)
        pos_ids = torch.arange(NUM_VISION_TOKENS, device=pixels.device)
        return tokens + self.pos(pos_ids)[None, :, :]


class FusedAttention(nn.Module):
    """Mission 01's Attention, generalized: an explicit mask instead of a
    hardcoded `is_causal=True`. `attn_mask=None` reproduces the exact causal
    behavior the text-only baseline needs; a real additive mask is what makes
    a vision prefix (bidirectional among itself, visible to every text
    position, never itself causally restricted) representable at all.
    """

    def __init__(self, cfg: Config):
        super().__init__()
        self.cfg = cfg
        self.n_rep = cfg.n_head // cfg.n_kv_head
        self.q = nn.Linear(cfg.d_model, cfg.n_head * cfg.d_head, bias=False)
        self.k = nn.Linear(cfg.d_model, cfg.n_kv_head * cfg.d_head, bias=False)
        self.v = nn.Linear(cfg.d_model, cfg.n_kv_head * cfg.d_head, bias=False)
        self.o = nn.Linear(cfg.n_head * cfg.d_head, cfg.d_model, bias=False)

    def forward(
        self, x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor, attn_mask: torch.Tensor | None
    ) -> torch.Tensor:
        B, T, _ = x.shape
        cfg = self.cfg
        q = self.q(x).view(B, T, cfg.n_head, cfg.d_head).transpose(1, 2)
        k = self.k(x).view(B, T, cfg.n_kv_head, cfg.d_head).transpose(1, 2)
        v = self.v(x).view(B, T, cfg.n_kv_head, cfg.d_head).transpose(1, 2)

        q, k = apply_rope(q, cos, sin), apply_rope(k, cos, sin)

        if self.n_rep > 1:
            k = k.repeat_interleave(self.n_rep, dim=1)
            v = v.repeat_interleave(self.n_rep, dim=1)

        if attn_mask is not None:
            out = F.scaled_dot_product_attention(q, k, v, attn_mask=attn_mask)
        else:
            out = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        return self.o(out.transpose(1, 2).contiguous().view(B, T, -1))

    def forward_with_weights(
        self, x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor, attn_mask: torch.Tensor | None
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Diagnostic-only twin of `forward`: recomputes the identical q/k/v/RoPE
        pipeline but with an explicit `q @ k.T / sqrt(d_head)` + softmax instead
        of `scaled_dot_product_attention`, which never exposes its weights. Used
        only by the attention-heatmap script below, never on the training path,
        so it cannot change training performance or numerics.
        """
        B, T, _ = x.shape
        cfg = self.cfg
        q = self.q(x).view(B, T, cfg.n_head, cfg.d_head).transpose(1, 2)
        k = self.k(x).view(B, T, cfg.n_kv_head, cfg.d_head).transpose(1, 2)
        v = self.v(x).view(B, T, cfg.n_kv_head, cfg.d_head).transpose(1, 2)

        q, k = apply_rope(q, cos, sin), apply_rope(k, cos, sin)

        if self.n_rep > 1:
            k = k.repeat_interleave(self.n_rep, dim=1)
            v = v.repeat_interleave(self.n_rep, dim=1)

        scores = (q @ k.transpose(-2, -1)) / math.sqrt(cfg.d_head)
        if attn_mask is not None:
            scores = scores + attn_mask
        weights = F.softmax(scores, dim=-1)
        out = weights @ v
        return self.o(out.transpose(1, 2).contiguous().view(B, T, -1)), weights


class Block(nn.Module):
    def __init__(self, cfg: Config):
        super().__init__()
        self.n1, self.n2 = RMSNorm(cfg.d_model), RMSNorm(cfg.d_model)
        self.attn, self.mlp = FusedAttention(cfg), SwiGLU(cfg)

    def forward(self, x, cos, sin, attn_mask):
        x = x + self.attn(self.n1(x), cos, sin, attn_mask)
        return x + self.mlp(self.n2(x))


class VisionLanguageTransformer(nn.Module):
    """`use_vision=False` reduces to a plain causal word-level decoder -- the
    text-only baseline mission 05's mission.yaml requires, sharing every class
    above with the vision pathway so the comparison isolates exactly the
    vision prefix, nothing else.
    """

    def __init__(self, cfg: Config, use_vision: bool):
        super().__init__()
        self.cfg = cfg
        self.use_vision = use_vision
        if use_vision:
            self.vision = VisionPatchEmbed(cfg)
        self.tok = nn.Embedding(cfg.vocab_size, cfg.d_model)
        self.blocks = nn.ModuleList([Block(cfg) for _ in range(cfg.n_layer)])
        self.norm = RMSNorm(cfg.d_model)
        self.head = nn.Linear(cfg.d_model, cfg.vocab_size, bias=False)
        self.tok.weight = self.head.weight  # tied

        self.apply(self._init)
        for name, p in self.named_parameters():
            if name.endswith(("o.weight", "down.weight")):
                nn.init.normal_(p, mean=0.0, std=0.02 / math.sqrt(2 * cfg.n_layer))

    @staticmethod
    def _init(m: nn.Module) -> None:
        if isinstance(m, (nn.Linear, nn.Embedding)):
            nn.init.normal_(m.weight, mean=0.0, std=0.02)

    @property
    def num_vision_tokens(self) -> int:
        return NUM_VISION_TOKENS if self.use_vision else 0

    def build_mask(self, text_valid_lens: torch.Tensor, text_len: int, device) -> torch.Tensor:
        """(B, 1, T, T) additive mask, T = num_vision_tokens + text_len.

        Vision positions attend to each other bidirectionally and never to
        text (a fixed image should not depend on which question was asked).
        Text positions attend causally to all vision positions plus every
        text position at or before their own -- and never to a padding key,
        which is per-example since valid text length varies.
        """
        nv = self.num_vision_tokens
        T = nv + text_len
        base = torch.full((T, T), NEG, device=device)
        if nv > 0:
            base[:nv, :nv] = 0.0
        causal = torch.tril(torch.ones(text_len, text_len, device=device)) == 1
        base[nv:, nv:][causal] = 0.0
        base[nv:, :nv] = 0.0  # every text position sees the full image
        B = text_valid_lens.shape[0]
        mask = base[None, None, :, :].expand(B, 1, T, T).clone()
        positions = torch.arange(text_len, device=device)[None, :]
        pad_key = positions >= text_valid_lens[:, None]  # (B, text_len)
        pad_additive = torch.zeros(B, text_len, device=device)
        pad_additive.masked_fill_(pad_key, NEG)
        mask[:, 0, :, nv:] = mask[:, 0, :, nv:] + pad_additive[:, None, :]
        return mask

    def forward(
        self,
        pixels: torch.Tensor | None,
        text_ids: torch.Tensor,
        text_valid_lens: torch.Tensor,
        targets: torch.Tensor | None = None,
    ):
        _batch, text_len = text_ids.shape
        device = text_ids.device
        text_tokens = self.tok(text_ids)
        if self.use_vision:
            assert pixels is not None
            x = torch.cat([self.vision(pixels), text_tokens], dim=1)
        else:
            x = text_tokens
        T = x.shape[1]
        cos, sin = build_rope_cache(T, self.cfg.d_head, self.cfg.rope_theta, device)
        mask = self.build_mask(text_valid_lens, text_len, device)
        for block in self.blocks:
            x = block(x, cos, sin, mask)
        logits_all = self.head(self.norm(x))
        logits = logits_all[:, self.num_vision_tokens :, :]
        if targets is None:
            return logits, None
        loss = F.cross_entropy(
            logits.reshape(-1, logits.size(-1)), targets.reshape(-1), ignore_index=IGNORE_INDEX
        )
        return logits, loss

    def forward_capturing_attention(
        self,
        pixels: torch.Tensor | None,
        text_ids: torch.Tensor,
        text_valid_lens: torch.Tensor,
        layer: int,
    ) -> torch.Tensor:
        """Diagnostic-only: identical token/vision embedding and mask setup as
        `forward`, but recomputes exactly one block's attention through
        `FusedAttention.forward_with_weights` so its post-softmax weights are
        observable. Every other block still runs the ordinary `forward` path
        unchanged. Returns `(n_head, T, T)` attention weights for that block.
        """
        _batch, text_len = text_ids.shape
        device = text_ids.device
        text_tokens = self.tok(text_ids)
        if self.use_vision:
            assert pixels is not None
            x = torch.cat([self.vision(pixels), text_tokens], dim=1)
        else:
            x = text_tokens
        T = x.shape[1]
        cos, sin = build_rope_cache(T, self.cfg.d_head, self.cfg.rope_theta, device)
        mask = self.build_mask(text_valid_lens, text_len, device)
        weights = None
        for i, block in enumerate(self.blocks):
            if i == layer:
                attn_out, weights = block.attn.forward_with_weights(block.n1(x), cos, sin, mask)
                x = x + attn_out
                x = x + block.mlp(block.n2(x))
            else:
                x = block(x, cos, sin, mask)
        assert weights is not None
        return weights[0]

    def param_report(self) -> str:
        total = sum(p.numel() for p in self.parameters())
        return f"use_vision={self.use_vision}  total params={total:,}"
