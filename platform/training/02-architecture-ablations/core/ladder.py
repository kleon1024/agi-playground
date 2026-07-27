"""Run one rung of the architecture ablation ladder across N seeds.

A single seed is not a weak result on a small model — it is no result, because
run-to-run variance at this scale routinely exceeds the effect an architecture
swap produces. This script always runs `--seeds` independent seeds per arm and
writes every one of them to the result file, not just their average.

It also refuses to write a result without a budget definition. The three
control arms in `model.py` (activation, gqa, depth-width) are all built to
hold total parameters equal — see each function's docstring for how — so
every result file from this script carries `"budget": "equal_params"`. That
field exists so nobody downstream mistakes an equal-parameter comparison for
an equal-FLOPs or equal-wall-clock one; see the README's opening section for
why those three routinely disagree.

This is a CPU smoke test, not a training run: `--steps` forward/backward
passes on synthetic random token batches, just enough to prove every arm
constructs, trains a step, and produces a finite loss. The status line in
each result file says so explicitly. No claim about which arm "won" belongs
in this file's output, because no arm has actually been trained yet — the
card this repository uses for real runs is mid-pretraining (see the README).

Usage:
    python ladder.py --rung activation --seeds 3 --steps 20 --out /tmp/result.json
    python ladder.py --rung gqa --seeds 3 --steps 20
    python ladder.py --rung depth-width --seeds 3 --steps 20
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, replace
from pathlib import Path

import torch
from model import (
    Transformer,
    VariantConfig,
    d_ff_for,
    depth_width_arms,
    gqa_arms,
    real_params,
)

RUNGS = ("norm", "position", "activation", "gqa", "depth-width")


def build_arms(rung: str, control: VariantConfig) -> dict[str, VariantConfig]:
    if rung == "norm":
        return {"rmsnorm": control, "layernorm": replace(control, norm="layernorm")}
    if rung == "position":
        return {
            "rope": control,
            "learned": replace(control, pos_scheme="learned"),
            "none": replace(control, pos_scheme="none"),
        }
    if rung == "activation":
        gelu_d_ff = d_ff_for("gelu", control.d_model)
        return {
            "swiglu": control,
            "gelu": replace(control, activation="gelu", d_ff=gelu_d_ff),
        }
    if rung == "gqa":
        return gqa_arms(control)
    if rung == "depth-width":
        return depth_width_arms(control, range(64, 1025, 8))
    raise ValueError(f"unknown rung {rung!r}; choose from {RUNGS}")


def smoke_train_one_seed(cfg: VariantConfig, seed: int, steps: int, batch: int) -> dict:
    """A few CPU steps on random tokens: proves the code path, nothing more."""
    torch.manual_seed(seed)
    model = Transformer(cfg)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)

    losses = []
    for _ in range(steps):
        x = torch.randint(0, cfg.vocab_size, (batch, cfg.block_size))
        y = torch.randint(0, cfg.vocab_size, (batch, cfg.block_size))
        _, loss = model(x, y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        losses.append(loss.item())

    return {"seed": seed, "losses": losses, "final_loss": losses[-1]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rung", choices=RUNGS, required=True)
    ap.add_argument("--seeds", type=int, default=3, help="independent seeds per arm")
    ap.add_argument("--steps", type=int, default=20, help="optimizer steps per seed, on CPU")
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--out", type=Path, default=None, help="write JSON here if set")
    args = ap.parse_args()

    control = VariantConfig()
    arms = build_arms(args.rung, control)

    result = {
        "rung": args.rung,
        "budget": "equal_params",
        "status": "smoke_test — CPU, random tokens, no training happened",
        "seeds": args.seeds,
        "steps_per_seed": args.steps,
        "arms": {},
    }

    started = time.perf_counter()
    for name, cfg in arms.items():
        arm_result = {
            "config": asdict(cfg),
            "real_params": real_params(cfg),
            "runs": [
                smoke_train_one_seed(cfg, seed=seed, steps=args.steps, batch=args.batch)
                for seed in range(args.seeds)
            ],
        }
        result["arms"][name] = arm_result
        print(
            f"{args.rung}/{name}: {arm_result['real_params']:,} params, "
            f"{args.seeds} seeds x {args.steps} steps ok"
        )
    result["wallclock_seconds"] = round(time.perf_counter() - started, 3)

    if args.out is not None:
        args.out.write_text(json.dumps(result, indent=2))
        print(f"wrote {args.out}")
    print(f"total wallclock: {result['wallclock_seconds']}s (this machine, this smoke test only)")


if __name__ == "__main__":
    main()
