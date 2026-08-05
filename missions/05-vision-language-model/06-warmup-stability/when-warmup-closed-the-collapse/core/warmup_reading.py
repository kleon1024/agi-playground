"""The warmup that closed the collapse: eval spread vs train-loss spread.

Stage 06's recorded run added a linear LR warmup and measured the eval
spread fall (0.2309 -> 0.0536). This script reads the recorded JSON and
lays out the two numbers that explain the mechanism: the per-seed eval
scores (the collapse closed) and the per-seed final train loss (which stays
wide), so "the warmup fixed the seed-2 collapse" is a contrast between what
the warmup changed and what it did not.

Input (recorded, unchanged): ../runs/warmup-results.json

Run:
    uv run python core/warmup_reading.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    with open(Path(__file__).resolve().parents[2] / "runs" / "warmup-results.json") as fh:
        d = json.load(fh)

    eval_ = d["eval_exact_match"]
    loss = d["final_train_loss"]
    base = d["stage01_baseline_eval_exact_match"]

    print(f"eval exact-match: warmup mean {eval_['mean']:.4f} spread {eval_['spread']:.4f} "
          f"per-seed {[round(x, 4) for x in eval_['per_seed']]}")
    print(f"stage-01 baseline (no warmup): mean {base['mean']:.4f} spread {base['spread']:.4f}")
    print(f"final train loss: mean {loss['mean']:.4f} spread {loss['spread']:.4f} "
          f"per-seed {[round(x, 4) for x in loss['per_seed']]}")
    print(f"\nreading: eval spread fell {base['spread']:.4f} -> {eval_['spread']:.4f}, "
          f"but train-loss spread stayed {loss['spread']:.4f} — the collapse was")
    print("an optimization-path issue (one seed diverged), not an irreducible")
    print("seed difference the loss itself would show.")


if __name__ == "__main__":
    main()
