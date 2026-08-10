"""The greedy baseline's ceiling, read from the recorded baselines run.

Stage 00's run measured random and greedy baselines on the grid-world.
The greedy one-step heuristic solved 82.4% — not 100% — and this chapter
reads the record to ask why a lookahead policy misses the rest.

Input (recorded, unchanged): ../runs/baselines.json

Run:
    uv run python core/greedy_read.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    with open(
        Path(__file__).resolve().parents[2] / "runs" / "baselines.json"
    ) as fh:
        d = json.load(fh)
    print("grid-world baselines (recorded), read:")
    for name in ("random", "greedy"):
        r = d["results"][name]
        print(f"  {name:<7} {r['successes']:>3}/{r['trials']} "
              f"({r['success_rate']:.3f}) mean {r['mean_steps_on_success']:.2f}")
    print(f"  board: {d['size']}x{d['size']}, {d['num_walls']} walls, "
          f"max_steps {d['max_steps']}")
    print("\nreading: greedy is one-step lookahead, so it can commit to a")
    print("dead end the step it enters — 82.4% is the ceiling of a policy")
    print("that cannot see around the corner, which is exactly the gap a")
    print("trained policy would have to close.")


if __name__ == "__main__":
    main()
