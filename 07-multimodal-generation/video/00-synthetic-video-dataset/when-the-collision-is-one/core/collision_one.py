"""The one-in-150 collision, read from the recorded dataset run.

Stage 00's generator extended mission 05's image space along a time axis,
and the collision problem shrank from hundreds to one. This script reads
the recorded run and lays out why.

Input (recorded, unchanged): ../runs/2026-07-31-dataset-gen.md

Run:
    uv run python core/collision_one.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-07-31-dataset-gen.md"
    ).read_text()
    print("the video-dataset collision story (recorded), read:")
    for row in re.findall(
        r"(only a single eval candidate needed rejecting[^\n]*|"
        r"\d+ train/eval collisions[^\n]*|"
        r"roughly two orders of magnitude[^\n]*|"
        r"3 shapes x 4 colors x 3 half-sizes x 8 directions[^\n]*)", run
    ):
        print(f"  {row.strip()}")
    print("\nreading: per-clip state space multiplies over the time axis, so")
    print("collisions that dominated mission 05's static images nearly vanish —")
    print("the generator's headroom is a property of the space, not the code.")


if __name__ == "__main__":
    main()
