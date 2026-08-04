"""A modern decoder-only transformer: RMSNorm, RoPE, SwiGLU, GQA.

[The first training loop](../../../../foundations/01-first-training-loop/)
built a GPT-2-shaped model: LayerNorm, learned position embeddings, a GELU
MLP. This file is the same skeleton with every one of those choices replaced by
what the field settled on afterwards. Read them as four independent arguments,
because that is what they are — each was adopted for its own reason, and each
can be ablated on its own:

1. **RMSNorm instead of LayerNorm.** LayerNorm subtracts the mean, then scales
   by the standard deviation, then applies a learned gain and bias. RMSNorm
   drops the mean subtraction and the bias, keeping only a rescale by the root
   mean square. It turns out the re-centering contributes little while costing
   a reduction pass over the features, so this is close to free throughput.

2. **RoPE instead of learned position embeddings.** A learned position table
   assigns each absolute index its own vector, so the model has no
   representation for position 4096 if it only ever trained to 2048 — the
   embedding simply does not exist. RoPE instead *rotates* the query and key
   vectors by an angle proportional to position, which makes the attention
   score depend on the **difference** of two positions rather than their
   absolute values. Relative structure generalizes; a lookup table does not.

3. **SwiGLU instead of a GELU MLP.** The standard MLP is `down(act(up(x)))`.
   SwiGLU splits the up-projection in two and lets one half gate the other:
   `down(silu(gate(x)) * up(x))`. That is three matrices instead of two, so the
   hidden dimension is conventionally shrunk to roughly 2/3 of 4d to hold the
   parameter count constant, making the comparison honest.

4. **GQA instead of full multi-head attention.** Every query head having its own
   key/value head is what makes the KV cache enormous at serving time. Grouped
   query attention shares one KV head across a group of query heads, shrinking
   the cache by exactly the group ratio. This is a *pretraining* decision made
   to buy *inference* headroom — see the
   [the serving stage](../../05-serve/).

Run `python model.py` to print the parameter budget without training anything.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
from torch import nn
from torch.nn import functional as F


@dataclass
class Config:
    # 16,384 BPE tokens + 1 document separator = 16,385, rounded up to the next
    # multiple of 128. Padding the vocabulary to a multiple of 64/128 lets the
    # output projection use tensor cores on a clean tile boundary; the unused
    # rows cost a rounding error in parameters and can measurably speed up the
    # largest matmul in the model. nanoGPT famously found the same win padding
    # GPT-2's 50,257 to 50,304.
    vocab_size: int = 16512
    n_layer: int = 12
    n_head: int = 12
    n_kv_head: int = 4      # < n_head enables GQA; == n_head is standard MHA
    d_model: int = 768
    d_ff: int = 2048        # ~2/3 * 4 * d_model, the SwiGLU convention
    block_size: int = 1024
    rope_theta: float = 10_000.0

    @property
    def d_head(self) -> int:
        return self.d_model // self.n_head


class RMSNorm(nn.Module):
    """Scale by root-mean-square. No mean subtraction, no bias."""

    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(dim))
        self.eps = eps

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Compute the norm in fp32 even under autocast: the sum of squares is
        # the one place in the block where bf16's narrow mantissa actually
        # costs accuracy.
        dtype = x.dtype
        x = x.float()
        x = x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps)
        return (x * self.weight.float()).to(dtype)


def build_rope_cache(seq_len: int, d_head: int, theta: float, device) -> tuple:
    """Precompute cos/sin tables for rotary embeddings.

    Frequencies decay geometrically across the head dimension, so early pairs
    rotate fast (encoding fine, local position) and later pairs rotate slowly
    (encoding coarse, long-range position). A position is therefore represented
    at many scales at once, much like binary place value.
    """
    inv_freq = 1.0 / (theta ** (torch.arange(0, d_head, 2, device=device).float() / d_head))
    pos = torch.arange(seq_len, device=device).float()
    freqs = torch.outer(pos, inv_freq)          # (T, d_head/2)
    return freqs.cos(), freqs.sin()


def apply_rope(x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
    """Rotate pairs of channels by the position-dependent angle.

    Treat consecutive channel pairs as 2D points and rotate each by theta*pos.
    Because a dot product between two rotated vectors depends only on the
    difference of their angles, the resulting attention score sees relative
    position for free — that is the entire trick.
    """
    # x: (B, n_head, T, d_head)
    x1, x2 = x.chunk(2, dim=-1)
    cos = cos[None, None, :, :]
    sin = sin[None, None, :, :]
    return torch.cat([x1 * cos - x2 * sin, x1 * sin + x2 * cos], dim=-1)


class Attention(nn.Module):
    def __init__(self, cfg: Config):
        super().__init__()
        self.cfg = cfg
        self.n_rep = cfg.n_head // cfg.n_kv_head
        self.q = nn.Linear(cfg.d_model, cfg.n_head * cfg.d_head, bias=False)
        self.k = nn.Linear(cfg.d_model, cfg.n_kv_head * cfg.d_head, bias=False)
        self.v = nn.Linear(cfg.d_model, cfg.n_kv_head * cfg.d_head, bias=False)
        self.o = nn.Linear(cfg.n_head * cfg.d_head, cfg.d_model, bias=False)

    def forward(self, x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
        B, T, _ = x.shape
        cfg = self.cfg
        q = self.q(x).view(B, T, cfg.n_head, cfg.d_head).transpose(1, 2)
        k = self.k(x).view(B, T, cfg.n_kv_head, cfg.d_head).transpose(1, 2)
        v = self.v(x).view(B, T, cfg.n_kv_head, cfg.d_head).transpose(1, 2)

        q, k = apply_rope(q, cos, sin), apply_rope(k, cos, sin)

        if self.n_rep > 1:
            # Repeat each KV head to face its group of query heads. Note this
            # expands a *view* for the kernel's benefit — the cache that
            # matters at inference time stays the small, unrepeated one.
            k = k.repeat_interleave(self.n_rep, dim=1)
            v = v.repeat_interleave(self.n_rep, dim=1)

        out = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        return self.o(out.transpose(1, 2).contiguous().view(B, T, -1))


class SwiGLU(nn.Module):
    def __init__(self, cfg: Config):
        super().__init__()
        self.gate = nn.Linear(cfg.d_model, cfg.d_ff, bias=False)
        self.up = nn.Linear(cfg.d_model, cfg.d_ff, bias=False)
        self.down = nn.Linear(cfg.d_ff, cfg.d_model, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.down(F.silu(self.gate(x)) * self.up(x))


class Block(nn.Module):
    def __init__(self, cfg: Config):
        super().__init__()
        self.n1, self.n2 = RMSNorm(cfg.d_model), RMSNorm(cfg.d_model)
        self.attn, self.mlp = Attention(cfg), SwiGLU(cfg)

    def forward(self, x, cos, sin):
        x = x + self.attn(self.n1(x), cos, sin)
        return x + self.mlp(self.n2(x))


class Transformer(nn.Module):
    def __init__(self, cfg: Config):
        super().__init__()
        self.cfg = cfg
        self.tok = nn.Embedding(cfg.vocab_size, cfg.d_model)
        self.blocks = nn.ModuleList([Block(cfg) for _ in range(cfg.n_layer)])
        self.norm = RMSNorm(cfg.d_model)
        self.head = nn.Linear(cfg.d_model, cfg.vocab_size, bias=False)
        self.tok.weight = self.head.weight  # tied

        self.apply(self._init)
        # Scale the residual-path output projections down by depth. Without
        # this the residual stream's variance grows with layer count and deep
        # models start unstable — the fix GPT-2 introduced and everything since
        # has kept.
        for name, p in self.named_parameters():
            if name.endswith(("o.weight", "down.weight")):
                nn.init.normal_(p, mean=0.0, std=0.02 / math.sqrt(2 * cfg.n_layer))

        self._cache: dict = {}

    @staticmethod
    def _init(m: nn.Module) -> None:
        if isinstance(m, (nn.Linear, nn.Embedding)):
            nn.init.normal_(m.weight, mean=0.0, std=0.02)

    def _rope(self, T: int, device):
        key = (T, device)
        if key not in self._cache:
            cos, sin = build_rope_cache(T, self.cfg.d_head, self.cfg.rope_theta, device)
            self._cache[key] = (cos, sin)
        return self._cache[key]

    def forward(self, idx: torch.Tensor, targets: torch.Tensor | None = None):
        _, T = idx.shape
        cos, sin = self._rope(T, idx.device)
        x = self.tok(idx)
        for block in self.blocks:
            x = block(x, cos, sin)
        logits = self.head(self.norm(x))
        if targets is None:
            return logits, None
        loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.reshape(-1))
        return logits, loss

    def param_report(self) -> str:
        cfg = self.cfg
        emb = cfg.vocab_size * cfg.d_model
        attn = cfg.d_model * (cfg.n_head + 2 * cfg.n_kv_head) * cfg.d_head + cfg.d_model**2
        mlp = 3 * cfg.d_model * cfg.d_ff
        per_layer = attn + mlp
        total = sum(p.numel() for p in self.parameters())
        lines = [
            f"{'component':<34}{'params':>14}",
            "-" * 48,
            f"{'embedding (tied with head)':<34}{emb:>14,}",
            f"{'per layer · attention (GQA)':<34}{attn:>14,}",
            f"{'per layer · SwiGLU':<34}{mlp:>14,}",
            f"{'per layer total':<34}{per_layer:>14,}",
            f"{f'x {cfg.n_layer} layers':<34}{per_layer * cfg.n_layer:>14,}",
            "-" * 48,
            f"{'TOTAL':<34}{total:>14,}  ({total / 1e6:.1f}M)",
            "",
            f"non-embedding params: {total - emb:,}",
            f"KV cache per token:   {2 * cfg.n_layer * cfg.n_kv_head * cfg.d_head * 2:,} bytes (bf16)",
            (
                f"  ... under full MHA:  "
                f"{2 * cfg.n_layer * cfg.n_head * cfg.d_head * 2:,} bytes "
                f"({cfg.n_head // cfg.n_kv_head}x more)"
            ),
        ]
        return "\n".join(lines)


if __name__ == "__main__":
    cfg = Config()
    model = Transformer(cfg)
    print(model.param_report())
    # Chinchilla's compute-optimal rule of thumb: about 20 tokens per parameter.
    n = sum(p.numel() for p in model.parameters())
    print(f"\nChinchilla-optimal tokens (~20x params): {20 * n / 1e9:.2f}B")
