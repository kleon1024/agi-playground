"""A tiny mixture-of-experts, with the routing statistics the line is about.

The MoE line (see the language-model lineage) is a set of bets on one
mechanism: route each input to a subset of expert networks, so capacity
grows with the number of experts while per-input compute grows with the
number routed to. This file trains a toy MoE on a synthetic pattern task and
measures the four things the real line cares about:

1. **Specialization.** Four input patterns, one target each. A top-1 router
   should force each expert to own one pattern; top-4 (dense) should not
   specialize at all.
2. **Load balance.** Pattern 0 appears four times as often as the others. A
   top-1 router that maximizes accuracy routes most inputs to expert 0 —
   the imbalance the load-balancing losses (and K3's Quantile Balancing)
   exist to fight.
3. **The shared expert.** An always-on expert absorbs the common structure,
   letting routed experts specialize on the difference — the design
   LatentMoE and modern MoE stacks use.
4. **Accuracy vs routing cost.** Top-1 and top-2 should match dense
   accuracy on this separable task while routing a fraction of the compute.

Everything is torch and numpy; no training loop machinery beyond what fits
in this file. The router is a linear layer + softmax, experts are two-layer
MLPs (the production SwiGLU variant is noted in the chapter, not
reimplemented here).

Run:
    uv run --group torch python core/moe_demo.py
"""

from __future__ import annotations

import argparse

import torch
from torch.nn import functional as F

N_PATTERNS = 4
D_MODEL = 24
N_EXPERTS = 4
HIDDEN = 32
STEPS = 1500
PATTERN_WEIGHTS = [4, 1, 1, 1]  # pattern 0 is four times as frequent


def make_data(rng: torch.Generator, n: int) -> tuple[torch.Tensor, torch.Tensor]:
    patterns = torch.tensor(PATTERN_WEIGHTS).float()
    p = patterns / patterns.sum()
    idx = torch.multinomial(p, n, replacement=True, generator=rng)
    x = torch.zeros(n, D_MODEL)
    # each pattern activates a distinct block of the input vector
    block = D_MODEL // N_PATTERNS
    for i in range(n):
        x[i, idx[i] * block : (idx[i] + 1) * block] = torch.randn(block, generator=rng) * 0.5 + 1.0
    y = F.one_hot(idx, N_PATTERNS).float()
    return x, y


class Expert(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(D_MODEL, HIDDEN),
            torch.nn.ReLU(),
            torch.nn.Linear(HIDDEN, N_PATTERNS),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class TinyMoE(torch.nn.Module):
    def __init__(self, top_k: int, shared: bool) -> None:
        super().__init__()
        self.top_k = top_k
        self.shared = shared
        self.router = torch.nn.Linear(D_MODEL, N_EXPERTS)
        self.experts = torch.nn.ModuleList([Expert() for _ in range(N_EXPERTS)])
        self.shared_expert = Expert() if shared else None

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        logits = self.router(x)
        probs = F.softmax(logits, dim=-1)
        topk = torch.topk(probs, self.top_k, dim=-1)
        out = torch.zeros(x.shape[0], N_PATTERNS)
        for j in range(self.top_k):
            k = topk.indices[:, j]
            out = out + topk.values[:, j, None] * torch.stack(
                [self.experts[k[i]](x[i : i + 1]).squeeze(0) for i in range(x.shape[0])]
            )
        if self.shared_expert is not None:
            out = out + self.shared_expert(x)
        return out, probs


def run(top_k: int, shared: bool, seed: int) -> dict:
    torch.manual_seed(seed)
    rng = torch.Generator().manual_seed(seed)
    train_x, train_y = make_data(rng, 800)
    test_x, test_y = make_data(rng, 200)
    model = TinyMoE(top_k, shared)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3)

    for step in range(STEPS):
        idx = torch.randperm(train_x.shape[0], generator=rng)[:64]
        out, _ = model(train_x[idx])
        loss = F.mse_loss(out, train_y[idx])
        opt.zero_grad()
        loss.backward()
        opt.step()

    model.eval()
    with torch.no_grad():
        out, probs = model(test_x)
        acc = float((out.argmax(dim=-1) == test_y.argmax(dim=-1)).float().mean())
        topk = torch.topk(probs, model.top_k, dim=-1)
        # an expert is counted as routed when it appears anywhere in the
        # top-k set, not only when it is the argmax winner
        routed = torch.zeros(test_x.shape[0], N_EXPERTS)
        for j in range(model.top_k):
            routed.scatter_(1, topk.indices[:, j : j + 1], 1.0)
        counts = routed.sum(dim=0).float()
        entropy = -((probs.mean(dim=0) + 1e-9) * torch.log(probs.mean(dim=0) + 1e-9)).sum()
        return {
            "top_k": top_k,
            "shared": shared,
            "accuracy": round(acc, 4),
            "routing_counts": counts.tolist(),
            "routing_entropy": round(float(entropy), 4),
            "load_imbalance": round(float(counts.max() / counts.min()), 3) if counts.min() > 0 else None,
        }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=20260806)
    args = ap.parse_args()

    print("tiny MoE, 4 experts, 4 patterns (pattern 0 four times as frequent)")
    print(f"{'top_k':>6} {'shared':>7} {'accuracy':>9} {'routing entropy':>16} {'load imbalance':>15}")
    for top_k in (1, 2, 4):
        for shared in (False, True):
            r = run(top_k, shared, args.seed)
            counts = ",".join(str(int(c)) for c in r["routing_counts"])
            print(
                f"{r['top_k']:>6} {r['shared']!s:>7} {r['accuracy']:>9.3f} "
                f"{r['routing_entropy']:>16.3f} {r['load_imbalance']!s:>15}  counts=[{counts}]"
            )


if __name__ == "__main__":
    main()
