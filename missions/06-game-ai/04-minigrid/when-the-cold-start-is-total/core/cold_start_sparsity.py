"""The cold start, quantified: baseline success and GRPO degeneracy.

Mission 06's three environments give a measured gradient in cold-start
severity: the grid-world's random policy succeeds 22.2% and only 1 of 200
GRPO steps is degenerate; MiniGrid's random policy succeeds 0.4% (2/500)
and all 80/80 steps per seed are degenerate; mission 01's arithmetic policy
has a near-zero well-formed-completion rate and 200/200 steps are
degenerate. This script assembles those recorded numbers into the one table
that explains the pattern: GRPO's group advantage needs reward variance,
and variance requires a baseline that sometimes succeeds.

Inputs (recorded): the stage run records' baseline numbers and the
minigrid-seed*.json degeneracy counts.

Run:
    uv run python core/cold_start_sparsity.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[2] / "runs"
    minigrid_degenerate = []
    for seed in (0, 1, 2):
        with open(root / f"minigrid-seed{seed}.json") as fh:
            d = json.load(fh)
        minigrid_degenerate.append(d["degenerate_steps"])

    print(f"{'environment':<30} {'random baseline':>15} {'degenerate steps':>17}")
    print(f"{'mission 01 arithmetic':<30} {'~0% (format)':>15} {'200/200':>17}")
    print(f"{'mission 06 grid-world':<30} {'22.2%':>15} {'1/200':>17}")
    print(f"{'mission 06 MiniGrid':<30} {'0.4% (2/500)':>15} {minigrid_degenerate!s:>17}")
    print("\nreading: degeneracy tracks baseline success — the group advantage")
    print("needs reward variance, and variance needs a policy that sometimes wins.")


if __name__ == "__main__":
    main()
