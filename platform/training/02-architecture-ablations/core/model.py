"""A small transformer whose norm, position scheme, activation, and KV head
count are config fields instead of decisions.

[Mission 01's pretraining model](../../../../missions/01-language-model-agent/02-pretrain/core/model.py)
frames RMSNorm, RoPE, SwiGLU, and GQA as four independent choices — "each can
be ablated on its own" — and then deliberately does not ablate them: that file
stays a fixed, readable reference. This file is that same block with each of
those four choices, plus depth-vs-width, turned into a `VariantConfig` field.
It does not import the mission's `model.py`, and the mission's `model.py` does
not import this — two different jobs, kept separate.

Every field here changes one thing:

- `norm`: RMSNorm drops LayerNorm's mean subtraction and bias, keeping only a
  rescale by the root-mean-square. Fewer reduction passes, no bias gradient.
- `pos_scheme`: RoPE rotates queries and keys by a position-dependent angle,
  so attention scores depend on relative position. `"learned"` adds a
  position-indexed embedding table instead — it has no representation for a
  position past what it trained on. `"none"` adds no positional signal at
  all; only the causal mask constrains order.
- `activation`: SwiGLU (`down(silu(gate(x)) * up(x))`) is three matrices
  against a GELU MLP's two (`down(gelu(up(x)))`), so an honest parameter-equal
  comparison has to shrink SwiGLU's `d_ff` — see `d_ff_for` below.
- `n_kv_head`: fewer KV heads than query heads is GQA. It shrinks the KV cache
  a group ratio at a time, at a pretraining-time cost this file lets you see
  directly in the parameter count.

Run `python model.py` to print every rung's parameter arithmetic without
training anything.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Literal

import torch
from torch import nn
from torch.nn import functional as F

Norm = Literal["rmsnorm", "layernorm"]
Position = Literal["rope", "learned", "none"]
Activation = Literal["swiglu", "gelu"]


@dataclass(frozen=True)
class VariantConfig:
    # Deliberately small: this file is read on a CPU, not deployed.
    vocab_size: int = 1024
    n_layer: int = 4
    n_head: int = 8
    n_kv_head: int = 8  # < n_head enables GQA
    d_model: int = 256
    d_ff: int = 683  # matched to SwiGLU by d_ff_for(); see below
    block_size: int = 128
    rope_theta: float = 10_000.0
    norm: Norm = "rmsnorm"
    pos_scheme: Position = "rope"
    activation: Activation = "swiglu"

    @property
    def d_head(self) -> int:
        return self.d_model // self.n_head


def d_ff_for(activation: Activation, d_model: int) -> int:
    """The `d_ff` that holds an MLP's parameter count equal across the swap.

    A GELU MLP is two matrices (`up`, `down`): `2 * d_model * d_ff` parameters.
    SwiGLU is three (`gate`, `up`, `down`): `3 * d_model * d_ff`. Shrinking
    SwiGLU's `d_ff` to 2/3 of GELU's keeps the two totals within a rounding
    error of each other. Skip this and the SwiGLU arm of the ladder is a
    bigger model, not a different activation.
    """
    base = 4 * d_model
    return round(base * 2 / 3) if activation == "swiglu" else base


def analytic_params(cfg: VariantConfig) -> int:
    """Parameter count from the config alone, no model instantiated.

    Mirrors the mission model's `param_report` arithmetic: tied embedding,
    attention (GQA-aware), and MLP (activation-aware). Omits norm weights —
    a few thousand parameters against a multi-million-parameter total — so
    this is the fast estimate a search loop uses; `real_params` below is the
    exact count once a model actually exists.
    """
    emb = cfg.vocab_size * cfg.d_model
    attn = cfg.d_model * (cfg.n_head + 2 * cfg.n_kv_head) * cfg.d_head + cfg.d_model**2
    mlp = 3 * cfg.d_model * cfg.d_ff if cfg.activation == "swiglu" else 2 * cfg.d_model * cfg.d_ff
    learned_pos = cfg.block_size * cfg.d_model if cfg.pos_scheme == "learned" else 0
    return emb + cfg.n_layer * (attn + mlp) + learned_pos


def real_params(cfg: VariantConfig) -> int:
    """Exact count from an instantiated model. Use this in anything reported."""
    return sum(p.numel() for p in Transformer(cfg).parameters())


class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(dim))
        self.eps = eps

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        dtype = x.dtype
        x = x.float()
        x = x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps)
        return (x * self.weight.float()).to(dtype)


def build_rope_cache(seq_len: int, d_head: int, theta: float, device) -> tuple:
    inv_freq = 1.0 / (theta ** (torch.arange(0, d_head, 2, device=device).float() / d_head))
    pos = torch.arange(seq_len, device=device).float()
    freqs = torch.outer(pos, inv_freq)
    return freqs.cos(), freqs.sin()


def apply_rope(x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
    x1, x2 = x.chunk(2, dim=-1)
    cos, sin = cos[None, None, :, :], sin[None, None, :, :]
    return torch.cat([x1 * cos - x2 * sin, x1 * sin + x2 * cos], dim=-1)


class Attention(nn.Module):
    def __init__(self, cfg: VariantConfig):
        super().__init__()
        self.cfg = cfg
        self.n_rep = cfg.n_head // cfg.n_kv_head
        self.q = nn.Linear(cfg.d_model, cfg.n_head * cfg.d_head, bias=False)
        self.k = nn.Linear(cfg.d_model, cfg.n_kv_head * cfg.d_head, bias=False)
        self.v = nn.Linear(cfg.d_model, cfg.n_kv_head * cfg.d_head, bias=False)
        self.o = nn.Linear(cfg.n_head * cfg.d_head, cfg.d_model, bias=False)

    def forward(self, x: torch.Tensor, rope) -> torch.Tensor:
        B, T, _ = x.shape
        cfg = self.cfg
        q = self.q(x).view(B, T, cfg.n_head, cfg.d_head).transpose(1, 2)
        k = self.k(x).view(B, T, cfg.n_kv_head, cfg.d_head).transpose(1, 2)
        v = self.v(x).view(B, T, cfg.n_kv_head, cfg.d_head).transpose(1, 2)

        if rope is not None:
            cos, sin = rope
            q, k = apply_rope(q, cos, sin), apply_rope(k, cos, sin)

        if self.n_rep > 1:
            k = k.repeat_interleave(self.n_rep, dim=1)
            v = v.repeat_interleave(self.n_rep, dim=1)

        out = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        return self.o(out.transpose(1, 2).contiguous().view(B, T, -1))


class SwiGLU(nn.Module):
    def __init__(self, cfg: VariantConfig):
        super().__init__()
        self.gate = nn.Linear(cfg.d_model, cfg.d_ff, bias=False)
        self.up = nn.Linear(cfg.d_model, cfg.d_ff, bias=False)
        self.down = nn.Linear(cfg.d_ff, cfg.d_model, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.down(F.silu(self.gate(x)) * self.up(x))


class GELUMLP(nn.Module):
    def __init__(self, cfg: VariantConfig):
        super().__init__()
        self.up = nn.Linear(cfg.d_model, cfg.d_ff, bias=False)
        self.down = nn.Linear(cfg.d_ff, cfg.d_model, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.down(F.gelu(self.up(x)))


class Block(nn.Module):
    def __init__(self, cfg: VariantConfig):
        super().__init__()
        norm_cls = RMSNorm if cfg.norm == "rmsnorm" else lambda dim: nn.LayerNorm(dim)
        self.n1, self.n2 = norm_cls(cfg.d_model), norm_cls(cfg.d_model)
        self.attn = Attention(cfg)
        self.mlp = SwiGLU(cfg) if cfg.activation == "swiglu" else GELUMLP(cfg)

    def forward(self, x, rope):
        x = x + self.attn(self.n1(x), rope)
        return x + self.mlp(self.n2(x))


class Transformer(nn.Module):
    def __init__(self, cfg: VariantConfig):
        super().__init__()
        self.cfg = cfg
        self.tok = nn.Embedding(cfg.vocab_size, cfg.d_model)
        self.pos = (
            nn.Embedding(cfg.block_size, cfg.d_model) if cfg.pos_scheme == "learned" else None
        )
        self.blocks = nn.ModuleList([Block(cfg) for _ in range(cfg.n_layer)])
        self.norm = RMSNorm(cfg.d_model) if cfg.norm == "rmsnorm" else nn.LayerNorm(cfg.d_model)
        self.head = nn.Linear(cfg.d_model, cfg.vocab_size, bias=False)
        self.tok.weight = self.head.weight  # tied

        self.apply(self._init)
        for name, p in self.named_parameters():
            if name.endswith(("o.weight", "down.weight")):
                nn.init.normal_(p, mean=0.0, std=0.02 / math.sqrt(2 * cfg.n_layer))

        self._rope_cache: dict = {}

    @staticmethod
    def _init(m: nn.Module) -> None:
        if isinstance(m, (nn.Linear, nn.Embedding)):
            nn.init.normal_(m.weight, mean=0.0, std=0.02)

    def _rope(self, T: int, device):
        if self.cfg.pos_scheme != "rope":
            return None
        key = (T, device)
        if key not in self._rope_cache:
            self._rope_cache[key] = build_rope_cache(T, self.cfg.d_head, self.cfg.rope_theta, device)
        return self._rope_cache[key]

    def forward(self, idx: torch.Tensor, targets: torch.Tensor | None = None):
        _, T = idx.shape
        rope = self._rope(T, idx.device)
        x = self.tok(idx)
        if self.pos is not None:
            x = x + self.pos(torch.arange(T, device=idx.device))[None, :, :]
        for block in self.blocks:
            x = block(x, rope)
        logits = self.head(self.norm(x))
        if targets is None:
            return logits, None
        loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.reshape(-1))
        return logits, loss


def gqa_arms(control: VariantConfig) -> dict[str, VariantConfig]:
    """KV head counts to try, all dividing `n_head` exactly."""
    return {
        f"kv{k}": replace(control, n_kv_head=k)
        for k in sorted({control.n_head, control.n_head // 2, control.n_head // 4, 1})
    }


def depth_width_arms(control: VariantConfig, candidate_widths: range) -> dict[str, VariantConfig]:
    """Depth/width pairs matched to the control's parameter count.

    For each candidate depth, search `candidate_widths` (restricted to
    multiples of `2 * n_head`, so `d_head` stays an even integer — RoPE
    rotates channel pairs, so an odd `d_head` cannot be split in half) for the
    width whose `analytic_params` lands closest to the control. The match is
    rarely exact — report the miss rather than rounding it away, the same
    discipline `platform/training/01-distributed` applies to ZeRO's uneven
    shard split.
    """
    target = analytic_params(control)
    arms = {}
    for n_layer in sorted({max(1, control.n_layer // 2), control.n_layer, control.n_layer * 2}):
        best_d_model = control.d_model
        best_gap = None
        for d_model in candidate_widths:
            if d_model % (2 * control.n_head) != 0:
                continue
            trial = replace(control, n_layer=n_layer, d_model=d_model)
            gap = abs(analytic_params(trial) - target)
            if best_gap is None or gap < best_gap:
                best_gap, best_d_model = gap, d_model
        arms[f"L{n_layer}-d{best_d_model}"] = replace(
            control, n_layer=n_layer, d_model=best_d_model
        )
    return arms


if __name__ == "__main__":
    control = VariantConfig()
    print(f"control: {control}")
    print(f"control real params: {real_params(control):,}\n")

    print("-- rung: activation (parameter-matched d_ff) --")
    gelu_d_ff = d_ff_for("gelu", control.d_model)
    gelu = replace(control, activation="gelu", d_ff=gelu_d_ff)
    print(f"swiglu d_ff={control.d_ff:<5} real params {real_params(control):,}")
    print(f"gelu   d_ff={gelu_d_ff:<5} real params {real_params(gelu):,}\n")

    print("-- rung: gqa (kv head count, parameters as a side effect) --")
    for name, cfg in gqa_arms(control).items():
        print(f"{name:<5} real params {real_params(cfg):,}")
    print()

    print("-- rung: depth-width (matched to control's parameter count) --")
    for name, cfg in depth_width_arms(control, range(64, 1025, 8)).items():
        n = real_params(cfg)
        delta = n - real_params(control)
        print(f"{name:<10} n_layer={cfg.n_layer:<3} d_model={cfg.d_model:<4} "
              f"real params {n:,} (delta {delta:+,})")
