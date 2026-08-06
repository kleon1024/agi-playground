"""The collapse that warmup closed, read from the recorded warmup JSON.

Stage 06's run retrained the vision pathway with a linear LR warmup and
compared against stage 01's baseline. This script reads the recorded JSON
and lays out the before/after on the two axes that matter: eval spread and
the seed that collapsed.

Input (recorded, unchanged): ../runs/warmup-results.json

Run:
    uv run python core/warmup_read.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    with open(
        Path(__file__).resolve().parents[2] / "runs" / "warmup-results.json"
    ) as fh:
        d = json.load(fh)
    new = d["eval_exact_match"]
    old = d["stage01_baseline_eval_exact_match"]
    print("warmup vs stage-01 baseline (recorded), read:")
    print(f"  stage 01: mean {old['mean']:.4f}, spread {old['spread']:.4f}, "
          f"seeds {[round(x,4) for x in old['per_seed']]}")
    print(f"  warmup:   mean {new['mean']:.4f}, spread {new['spread']:.4f}, "
          f"seeds {[round(x,4) for x in new['per_seed']]}")
    print(f"  warmup config: {d['warmup_frac']*100:.0f}% linear warmup over "
          f"{d['warmup_steps']} of {d['total_steps']} steps")
    print("\nreading: the collapse was the seed-2 outlier (0.2844), and warmup")
    print("closed it — spread tightens 0.2309 -> 0.0536 and mean rises")
    print("0.4375 -> 0.4970, so the fix is a training-dynamics one.")


if __name__ == "__main__":
    main()
