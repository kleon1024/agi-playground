"""The collision that closed the gap, read from the recorded dataset run.

Stage 00's first dataset generation used disjoint seed ranges and still
produced 116 pixel-identical train/eval collisions — plus a second defect
collisions alone did not reveal: the eval single-shape bucket came out
empty. This script reads the record and lays out both defects and the fix.

Input (recorded, unchanged): ../runs/2026-07-31-dataset-gen.md

Run:
    uv run python core/collision_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-07-31-dataset-gen.md"
    ).read_text()
    print("the dataset-generation defects (recorded), read:")
    coll = re.search(r"\| \*\*Pixel-hash collisions, train vs eval\*\* \| \*\*(\d+)\*\* \|", run)
    if coll:
        print(f"  collisions under disjoint seed ranges: {coll.group(1)}")
    empty = re.search(r"single-shape bucket came out empty", run)
    if empty:
        print("  second defect: the eval single-shape bucket came out empty")
    fix = re.search(r"(Widening each shape's size and position space[^.]*)", run)
    if fix:
        print(f"  fix: {fix.group(1)}.")
    print("\nreading: disjoint seeds are not disjoint images — the state space")
    print("is small enough that collisions happen across streams, and the")
    print("leakage guardrail must check pixels, not seeds.")


if __name__ == "__main__":
    main()
