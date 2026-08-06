"""The two baselines, read: what random and greedy each measure.

Stage 00's recorded baselines.json holds the two numbers a trained policy
must clear: random solves 22.2% of boards, greedy one-step solves 82.4%.
This script reads the committed JSON and lays out what each baseline
actually measures — including why random is not near zero on a mostly-open
5x5 board with four walls.

Input (recorded, unchanged): ../runs/baselines.json

Run:
    uv run python core/baseline_read.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    with open(Path(__file__).resolve().parents[2] / "runs" / "baselines.json") as fh:
        d = json.load(fh)
    print(f"gridworld: {d['size']}x{d['size']}, {d['num_walls']} walls, "
          f"{d['trials']} trials per baseline")
    for name in ("random", "greedy"):
        r = d["results"][name]
        print(
            f"  {name:<7} {r['successes']:>3}/{r['trials']} "
            f"({r['success_rate']:.3f})  mean {r['mean_steps_on_success']:.2f} steps"
        )
    print("\nreading: random is the no-learning floor and it is not near zero,")
    print("because a mostly-open board rewards persistence; greedy is the")
    print("one-step lookahead bar that actually separates trained from untrained.")


if __name__ == "__main__":
    main()
