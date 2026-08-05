"""The 2x2, read from the three recorded factorial seeds.

Stage 06 crossed dead-code reset with the EMA codebook update. This script
reads the three recorded seeds' four arms and the recorded main effects,
and lays out which half of the fix carried the work — the question the
stage exists to answer.

Inputs (recorded, unchanged): ../runs/factorial-codec-seed{0,1,2}.json

Run:
    uv run python core/factorial_grid.py
"""

from __future__ import annotations

import json
from pathlib import Path

ARMS = ("plain", "reset-only", "ema-only", "reset+ema")


def main() -> None:
    root = Path(__file__).resolve().parents[2] / "runs"
    print(f"{'arm':<12} " + " ".join(f"seed{s} MSE" for s in (0, 1, 2)))
    for arm in ARMS:
        mses = []
        for seed in (0, 1, 2):
            with open(root / f"factorial-codec-seed{seed}.json") as fh:
                d = json.load(fh)
            mses.append(round(d["arms"][arm]["eval_mse"], 4))
        print(f"{arm:<12} " + " ".join(f"{m:.4f}" for m in mses))

    with open(root / "factorial-codec-seed0.json") as fh:
        me = json.load(fh)["main_effects"]
    print("\nmain effects (seed 0, recorded):")
    print(f"  reset without EMA: {me['reset_effect_without_ema']['d_eval_mse']:+.4f} MSE, "
          f"{me['reset_effect_without_ema']['d_unique_codes']:+d} codes")
    print(f"  EMA without reset: {me['ema_effect_without_reset']['d_eval_mse']:+.4f} MSE, "
          f"{me['ema_effect_without_reset']['d_unique_codes']:+d} codes")
    print("\nreading: reset is the mechanism that did the work — EMA alone")
    print("makes things worse; EMA only enhances when the reset is present.")


if __name__ == "__main__":
    main()
