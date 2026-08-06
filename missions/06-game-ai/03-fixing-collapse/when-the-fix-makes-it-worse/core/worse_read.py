"""The fix that made it worse, read from the recorded collapse sweep.

Stage 03 tried two fixes for the collapse: a smaller group and an entropy
bonus. The recorded sweep shows both failed, and one made it strictly
worse. This script reads the record and lays out the per-variant results.

Input (recorded, unchanged): ../runs/2026-08-01-collapse-fix-sweep.md

Run:
    uv run python core/worse_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-08-01-collapse-fix-sweep.md"
    ).read_text()
    print("collapse-fix sweep (recorded), read:")
    for row in re.findall(
        r"\| ([\w-]+ \([\w= .]+\)|baseline \([\w,= .]+\)) \| ([\d/]+) \| ([\d.]+) \| ([\d.]+) \|",
        run,
    ):
        print(f"  {row[0]}: degenerate {row[1]}, greedy {row[2]}, sampled {row[3]}")
    worse = re.search(r"(strictly worse collapse[^.]*\.)", run)
    if worse:
        print(f"\n  {worse.group(1)}")
    print("\nreading: both fixes failed, and small-group made the collapse")
    print("strictly worse (single-character completions) — a recorded null")
    print("that says the training signal, not the group size, is the wall.")


if __name__ == "__main__":
    main()
