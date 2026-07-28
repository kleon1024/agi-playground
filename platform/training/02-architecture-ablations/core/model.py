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
FFN = Literal["dense", "moe"]


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

    # Mixture-of-experts. `ffn="moe"` replaces each block's single MLP with
    # `n_routed_expert` narrow ones plus `n_shared_expert` that every token
    # goes through, routing each token to `n_active_expert` of the routed set.
    # `expert_d_ff` is each expert's width; leave it None to derive a width
    # that holds active parameters equal to the dense arm (see `moe_arms`).
    ffn: FFN = "dense"
    n_routed_expert: int = 8
    n_active_expert: int = 2
    n_shared_expert: int = 1
    expert_d_ff: int | None = None

    @property
    def d_head(self) -> int:
        return self.d_model // self.n_head

    @property
    def expert_width(self) -> int:
        return self.expert_d_ff if self.expert_d_ff is not None else self.d_ff


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
    mlp = ffn_params(cfg)["total"]
    learned_pos = cfg.block_size * cfg.d_model if cfg.pos_scheme == "learned" else 0
    return emb + cfg.n_layer * (attn + mlp) + learned_pos


def ffn_params(cfg: VariantConfig) -> dict[str, int]:
    """One block's feed-forward parameters, split into total and active.

    For a dense block these are the same number. For an MoE block they are
    not, and the gap is the entire reason the arm exists: total parameters
    decide how much the model can store, active parameters decide what a token
    costs to compute. Any comparison that quotes one without the other is
    reporting half a result.
    """
    per_matrix = 3 if cfg.activation == "swiglu" else 2
    if cfg.ffn == "dense":
        n = per_matrix * cfg.d_model * cfg.d_ff
        return {"total": n, "active": n}
    expert = per_matrix * cfg.d_model * cfg.expert_width
    router = cfg.d_model * cfg.n_routed_expert
    return {
        "total": (cfg.n_routed_expert + cfg.n_shared_expert) * expert + router,
        "active": (cfg.n_active_expert + cfg.n_shared_expert) * expert + router,
    }


def active_params(cfg: VariantConfig) -> int:
    """Parameters a single token actually passes through.

    Equal to `analytic_params` for a dense model. For MoE it is smaller, and it
    is the number that predicts training and inference FLOPs.
    """
    attn = cfg.d_model * (cfg.n_head + 2 * cfg.n_kv_head) * cfg.d_head + cfg.d_model**2
    learned_pos = cfg.block_size * cfg.d_model if cfg.pos_scheme == "learned" else 0
    return (
        cfg.vocab_size * cfg.d_model
        + cfg.n_layer * (attn + ffn_params(cfg)["active"])
        + learned_pos
    )


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


class MoE(nn.Module):
    """Fine-grained experts with a shared expert and bias-corrected routing.

    Three decisions here, and each is a place the arm could have been built
    differently:

    **Fine-grained experts.** `n_routed_expert` narrow experts of width
    `expert_width`, of which `n_active_expert` run per token. Splitting a
    given active-parameter budget across more, smaller experts gives the
    router more combinations to choose from than a few wide ones do.

    **A shared expert.** `n_shared_expert` experts run for every token,
    unrouted. Without one, each routed expert has to relearn whatever is
    common to all tokens, spending specialist capacity on general work.

    **Bias-corrected load balancing, not an auxiliary loss.** Routing is
    discrete, so a router that starts favouring a few experts keeps favouring
    them, and the rest are never trained. The classical fix adds a
    load-balancing term to the loss, which pushes against the language
    objective and trades a little quality for balance. Instead each expert
    carries a scalar `bias` used *only* to pick the top-k, never to weight the
    output: overloaded experts have theirs nudged down, underloaded ones up,
    once per step. The gradient of the language objective is untouched.

    The dispatch below is a loop over experts, which is readable and slow.
    Production kernels group tokens by expert and run one batched matmul; the
    arithmetic is identical and the wall-clock is not, which is why this file
    is for measuring quality per parameter rather than tokens per second.
    """

    def __init__(self, cfg: VariantConfig):
        super().__init__()
        self.cfg = cfg
        expert_cfg = replace(cfg, d_ff=cfg.expert_width)
        make = (lambda: SwiGLU(expert_cfg)) if cfg.activation == "swiglu" else (lambda: GELUMLP(expert_cfg))
        self.experts = nn.ModuleList([make() for _ in range(cfg.n_routed_expert)])
        self.shared = nn.ModuleList([make() for _ in range(cfg.n_shared_expert)])
        self.router = nn.Linear(cfg.d_model, cfg.n_routed_expert, bias=False)
        # Not a parameter: it is updated by a rule, not by a gradient.
        self.register_buffer("bias", torch.zeros(cfg.n_routed_expert))
        self.register_buffer("load", torch.zeros(cfg.n_routed_expert))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, T, C = x.shape
        flat = x.reshape(-1, C)
        scores = torch.sigmoid(self.router(flat))
        _, chosen = torch.topk(scores + self.bias, self.cfg.n_active_expert, dim=-1)

        # Renormalise over the chosen experts only, so a token's routed
        # contribution has a consistent scale however confident the router was.
        picked = scores.gather(-1, chosen)
        weights = picked / picked.sum(-1, keepdim=True).clamp_min(1e-9)

        out = torch.zeros_like(flat)
        for e, expert in enumerate(self.experts):
            hit = chosen == e
            if not hit.any():
                continue
            rows = hit.any(-1).nonzero(as_tuple=True)[0]
            w = (weights * hit).sum(-1)[rows].unsqueeze(-1)
            out[rows] += w * expert(flat[rows])
            if self.training:
                self.load[e] += rows.numel()

        for expert in self.shared:
            out = out + expert(flat)
        return out.reshape(B, T, C)

    @torch.no_grad()
    def rebalance(self, gamma: float = 1e-3) -> None:
        """Nudge each expert's selection bias toward the mean load.

        Call once per optimizer step. `gamma` is a step size on the routing
        score, not on a parameter — too large and routing oscillates, too small
        and a collapsed router never recovers.
        """
        if self.load.sum() == 0:
            return
        mean = self.load.mean()
        self.bias += gamma * torch.sign(mean - self.load)
        self.load.zero_()


class Block(nn.Module):
    def __init__(self, cfg: VariantConfig):
        super().__init__()
        norm_cls = RMSNorm if cfg.norm == "rmsnorm" else lambda dim: nn.LayerNorm(dim)
        self.n1, self.n2 = norm_cls(cfg.d_model), norm_cls(cfg.d_model)
        self.attn = Attention(cfg)
        if cfg.ffn == "moe":
            self.mlp: nn.Module = MoE(cfg)
        else:
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


def moe_arms(control: VariantConfig) -> dict[str, VariantConfig]:
    """Dense against MoE under both budget definitions, because they disagree.

    A mixture-of-experts block has two parameter counts, and which one you hold
    equal decides the answer before the run starts:

    - **`moe-equal-active`** sizes each expert so a token passes through the
      same number of parameters as the dense arm. Compute per token matches;
      total parameters do not, by roughly the expert count. This is the arm
      that asks "for the same FLOPs, does extra stored capacity help?" — the
      question MoE was invented to answer yes to at scale.
    - **`moe-equal-total`** sizes each expert so the block holds the same
      parameters as the dense arm in total. Now storage matches and a token
      passes through roughly `(n_active + n_shared) / (n_routed + n_shared)` of
      them, so the MoE arm is *cheaper* per token. This asks the opposite
      question: "for the same memory, how much compute can routing save?"

    Reporting one of these as "MoE beat dense" without saying which is the
    single most common way this comparison is misread. The ladder refuses to
    let you: both arms are returned together.

    Expert widths are rounded to a multiple of 8, so the miss against the
    target is reported rather than hidden — the same discipline
    `depth_width_arms` applies.
    """
    def round8(x: float) -> int:
        return max(8, round(x / 8) * 8)

    routed, shared, active = control.n_routed_expert, control.n_shared_expert, control.n_active_expert
    return {
        "dense": replace(control, ffn="dense"),
        "moe-equal-active": replace(
            control, ffn="moe", expert_d_ff=round8(control.d_ff / (active + shared))
        ),
        "moe-equal-total": replace(
            control, ffn="moe", expert_d_ff=round8(control.d_ff / (routed + shared))
        ),
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

    print("-- rung: moe (two budget definitions, which disagree) --")
    arms = moe_arms(control)
    base_total, base_active = analytic_params(arms["dense"]), active_params(arms["dense"])
    for name, cfg in arms.items():
        total, act = analytic_params(cfg), active_params(cfg)
        print(f"{name:<18} expert_d_ff={cfg.expert_width:<5} "
              f"total {total:>10,} ({total / base_total - 1:+6.1%})  "
              f"active {act:>10,} ({act / base_active - 1:+6.1%})")
    print("both counts are analytic (norm weights omitted) so the two columns "
          "are comparable;\nthe percentage misses are expert widths rounded to "
          "a multiple of 8, reported rather than hidden.\n")

    print("-- rung: depth-width (matched to control's parameter count) --")
    for name, cfg in depth_width_arms(control, range(64, 1025, 8)).items():
        n = real_params(cfg)
        delta = n - real_params(control)
        print(f"{name:<10} n_layer={cfg.n_layer:<3} d_model={cfg.d_model:<4} "
              f"real params {n:,} (delta {delta:+,})")
