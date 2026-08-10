"""The flips that separate the optimizers, read from the recorded JSON.

The optimizer comparison ran SGD, momentum, and Adam on the same
ill-conditioned bowl (A=100, B=1). The recorded JSON holds the step counts
and the sign-flip counts on the steep axis. This script reads it and lays
out the mechanism: momentum and Adam are faster because they stop
oscillating across the steep direction, and the flip count is the direct
measure of that.

Input (recorded, unchanged): ../runs/optimizer-comparison.json

Run:
    uv run python core/flip_read.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    with open(
        Path(__file__).resolve().parents[2] / "runs" / "optimizer-comparison.json"
    ) as fh:
        d = json.load(fh)
    print(f"bowl: A={d['surface']['A']} B={d['surface']['B']} "
          f"condition number {d['surface']['condition_number']}")
    print(f"  {'optimizer':<9} {'steps':>6} {'steep-axis flips':>17} {'flips/steps':>11}")
    for name in ("sgd", "momentum", "adam"):
        o = d[name]
        print(
            f"  {name:<9} {o['steps_to_converge']:>6} "
            f"{o['sign_flips_on_steep_axis']:>17} "
            f"{o['sign_flips_on_steep_axis']/o['steps_to_converge']:>10.2f}"
        )
    print("\nreading: the step count and the flip count move together — momentum")
    print("damps the oscillation across the steep axis (341 -> 47 flips), Adam")
    print("nearly removes it (4), and fewer flips is what makes fewer steps possible.")


if __name__ == "__main__":
    main()
