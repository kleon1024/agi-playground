"""The solvability check, read from the recorded MiniGrid run.

Stage 04's cold-start result is only meaningful if the task is solvable.
The recorded run proves it twice: a hand-scripted sequence and a wall-
following policy both reach the goal. This script reads the record and
lays out the two checks and the random floor.

Input (recorded, unchanged): ../runs/2026-08-01-minigrid-cold-start.md

Run:
    uv run python core/solvability_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2]
        / "runs"
        / "2026-08-01-minigrid-cold-start.md"
    ).read_text()
    print("MiniGrid solvability checks (recorded), read:")
    for row in re.findall(
        r"(hand-scripted 9-action sequence[^\n]*|"
        r"[\d]+/[\d]+ = [\d.]+% success[^\n]*)", run
    ):
        print(f"  {row.strip()}")
    print("\nreading: the task is solvable (100% under wall-following), so a")
    print("cold-start failure is the training, not the environment — the")
    print("solvability check is what makes the null result attributable.")


if __name__ == "__main__":
    main()
