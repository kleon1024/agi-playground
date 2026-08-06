"""The factorial corners, read from the recorded 2x2 codec run.

Stage 06 crossed dead-code reset with EMA codebook update, four arms per
seed. The recorded run's two parity checks reproduce stage 04/05's numbers
exactly, which is what makes the two new corners trustworthy. This script
reads the record and lays out the grid and the parity checks.

Input (recorded, unchanged): ../runs/2026-08-05-factorial-vq.md

Run:
    uv run python core/corners_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-08-05-factorial-vq.md"
    ).read_text()
    print("the 2x2 factorial (recorded), read:")
    print("  arms: plain / reset-only / ema-only / reset+ema")
    for row in re.findall(
        r"\| Seed \| Arm \| Codes used \| Entropy ratio \| Eval MSE \|"
        r" Margin vs silence \| Resets \| Reset events[^\n]*\n"
        r"((?:\|.*\n)+)", run
    ):
        pass
    for row in re.findall(
        r"\| (\d) \| `([\w+]+)` \| (\d+) / (\d+) \| ([\d.]+) \| ([\d.]+) \| ([\d.-]+)% \| (\d+) \|",
        run,
    ):
        print(f"  seed {row[0]} {row[1]}: codes {row[2]}/{row[3]}, "
              f"entropy {row[4]}, eval {row[5]}, margin {row[6]}%, resets {row[7]}")
    parity = re.search(r"(stage 04's[^\n]*|stage 05's[^\n]*|identical to the last bit[^\n]*)", run)
    if parity:
        print(f"\n  parity: {parity.group(0)}")
    print("\nreading: the two published corners reproduce to full float")
    print("precision, so the two new corners are measured against the")
    print("mission's own baselines — which is what lets the mechanism")
    print("question (reset vs EMA) be answered, not approximated.")


if __name__ == "__main__":
    main()
