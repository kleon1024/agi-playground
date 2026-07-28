"""Train every arm of one rung, on real tokens, for a fixed budget, across seeds.

[`ladder.py`](ladder.py) proves each arm constructs and takes a step. It says
so in its own status field and it cannot rank anything, because nothing was
trained. This file is the instrument that can: same data, same budget, same
schedule, one architectural difference, repeated across seeds.

Three rules it enforces, because each one is a way a comparison like this
silently becomes worthless:

**Seeds, not a seed.** Run-to-run variance at this scale routinely exceeds the
effect an architecture swap produces. Every arm runs `--seeds` times and every
run is written out. The reported quantity is the arm difference *relative to
the seed spread*, and "smaller than the spread" is a result, not a failure.

**A declared budget.** Which quantity is held equal — total parameters, active
parameters, or tokens — decides the answer before training starts, and the
three routinely disagree. The output file carries `budget` as a required field
so no downstream reader has to guess.

**The same data, in the same order, per seed.** Arms share a seed's batch
sequence exactly, so a difference between arms cannot be a difference in what
they were shown. Seeds differ from each other; arms within a seed do not.

Usage:
    python ablate.py --rung moe --data ~/tokens --seeds 3 --tokens 1e8 --out result.json
"""

from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
import torch
from ladder import build_arms
from model import MoE, Transformer, VariantConfig, active_params, real_params


def batches(data: np.memmap, batch: int, block: int, steps: int, device: str, seed: int):
    """Deterministic batch sequence for a seed, identical across arms."""
    rng = np.random.default_rng(seed)
    for _ in range(steps):
        starts = rng.integers(0, len(data) - block - 1, size=batch)
        x = np.stack([data[s : s + block].astype(np.int64) for s in starts])
        y = np.stack([data[s + 1 : s + 1 + block].astype(np.int64) for s in starts])
        yield (
            torch.from_numpy(x).to(device, non_blocking=True),
            torch.from_numpy(y).to(device, non_blocking=True),
        )


@torch.no_grad()
def evaluate(model, data, batch, block, device, iters, seed) -> float:
    model.eval()
    total = 0.0
    for x, y in batches(data, batch, block, iters, device, seed):
        with torch.autocast("cuda", dtype=torch.bfloat16):
            _, loss = model(x, y)
        total += loss.item()
    model.train()
    return total / iters


def train_one(cfg: VariantConfig, seed: int, train_data, val_data, args) -> dict:
    torch.manual_seed(seed)
    device = args.device
    model = Transformer(cfg).to(device)
    moes = [m for m in model.modules() if isinstance(m, MoE)]

    steps = int(args.tokens / (args.batch * cfg.block_size))
    opt = torch.optim.AdamW(
        model.parameters(), lr=args.lr, betas=(0.9, 0.95), weight_decay=0.1,
        fused=(device == "cuda"),
    )
    warmup = max(1, steps // 50)

    history, started = [], time.perf_counter()
    for step, (x, y) in enumerate(batches(train_data, args.batch, cfg.block_size, steps, device, seed)):
        # Cosine schedule to a tenth of peak, warmed up. Identical for every
        # arm: a schedule tuned per arm would be a second difference.
        if step < warmup:
            lr = args.lr * (step + 1) / warmup
        else:
            progress = (step - warmup) / max(1, steps - warmup)
            lr = args.lr * (0.1 + 0.45 * (1 + math.cos(math.pi * progress)))
        for group in opt.param_groups:
            group["lr"] = lr

        with torch.autocast("cuda", dtype=torch.bfloat16):
            _, loss = model(x, y)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        opt.zero_grad(set_to_none=True)
        # Routing balance is maintained by a rule, not by the loss. See MoE.
        for moe in moes:
            moe.rebalance()

        if step % max(1, steps // 10) == 0 or step == steps - 1:
            history.append({"step": step, "train_loss": round(loss.item(), 4)})

    # Validation seed is fixed, so every arm and every seed is scored on the
    # same held-out batches. Only training differs.
    val = evaluate(model, val_data, args.batch, cfg.block_size, device, args.eval_iters, seed=999)
    return {
        "seed": seed,
        "val_loss": round(val, 4),
        "final_train_loss": history[-1]["train_loss"],
        "history": history,
        "wallclock_s": round(time.perf_counter() - started, 1),
        "tokens": steps * args.batch * cfg.block_size,
    }


def summarise(runs: list[dict]) -> dict:
    losses = [r["val_loss"] for r in runs]
    mean = sum(losses) / len(losses)
    spread = max(losses) - min(losses)
    return {"mean_val_loss": round(mean, 4), "seed_spread": round(spread, 4), "seeds": losses}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rung", required=True)
    ap.add_argument("--data", type=Path, required=True, help="directory with train.bin and val.bin")
    ap.add_argument("--budget", default="declared_in_rung",
                    help="which quantity is held equal; written into the result file")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--tokens", type=float, default=1e8, help="training tokens per seed per arm")
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--eval-iters", type=int, default=40)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--vocab-size", type=int, default=16512)
    ap.add_argument("--d-model", type=int, default=512)
    ap.add_argument("--n-layer", type=int, default=8)
    ap.add_argument("--n-head", type=int, default=8)
    ap.add_argument("--block-size", type=int, default=512)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    control = VariantConfig(
        vocab_size=args.vocab_size, d_model=args.d_model, n_layer=args.n_layer,
        n_head=args.n_head, n_kv_head=args.n_head, block_size=args.block_size,
        d_ff=round(4 * args.d_model * 2 / 3 / 8) * 8,
    )
    arms = build_arms(args.rung, control)

    train_data = np.memmap(args.data / "train.bin", dtype=np.uint16, mode="r")
    val_data = np.memmap(args.data / "val.bin", dtype=np.uint16, mode="r")

    result = {
        "rung": args.rung,
        "budget": args.budget,
        "status": "trained",
        "control": asdict(control),
        "tokens_per_run": args.tokens,
        "seeds": args.seeds,
        "arms": {},
    }
    print(f"{'arm':<20}{'total':>12}{'active':>12}{'val loss':>28}{'spread':>9}")
    for name, cfg in arms.items():
        runs = [train_one(cfg, s, train_data, val_data, args) for s in range(args.seeds)]
        stats = summarise(runs)
        result["arms"][name] = {
            "config": asdict(cfg), "real_params": real_params(cfg),
            "active_params": active_params(cfg), "runs": runs, **stats,
        }
        seeds_str = " ".join(f"{v:.4f}" for v in stats["seeds"])
        print(f"{name:<20}{real_params(cfg):>12,}{active_params(cfg):>12,}"
              f"{seeds_str:>28}{stats['seed_spread']:>9.4f}")
        if args.out:
            args.out.write_text(json.dumps(result, indent=2))

    if args.out:
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
