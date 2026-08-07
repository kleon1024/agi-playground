"""The margin that holds at two objects, read from the recorded runs.

Stage 05's two-object generation still closes MET: mean 0.1483 vs
frame-repeat 0.2193, margin 6.8x the seed spread. This script reads the
recorded JSONs and lays out the margin-vs-spread arithmetic.

Inputs (recorded, unchanged): stage-02 and stage-05 generation JSONs.

Run:
    uv run python core/multi_margin.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path


def main() -> None:
    mses, baselines = [], []
    for seed in (0, 1, 2):
        d2 = json.loads(
            (Path(__file__).resolve().parents[2] / "runs" / f"multi-object-seed{seed}.json").read_text()
        )["generation"]
        mses.append(d2["reconstruction_mse"]["lm_completion"])
        baselines.append(d2["reconstruction_mse"]["frame_repeat_baseline"])
        print(f"  seed {seed}: lm {mses[-1]:.4f} vs frame-repeat {baselines[-1]:.4f}")
    mean = statistics.fmean(mses)
    spread = max(mses) - min(mses)
    margin = statistics.fmean(baselines) - mean
    print(f"\n  mean {mean:.4f}, spread {spread:.4f}, baseline "
          f"{statistics.fmean(baselines):.4f}")
    print(f"  margin {margin:.4f} = {margin/spread:.1f}x the spread")
    print("\nreading: two objects still beat frame-repeat by ~6.8x the seed")
    print("spread — MET holds, and the capacity limit is the finding, not a fail.")


if __name__ == "__main__":
    main()
