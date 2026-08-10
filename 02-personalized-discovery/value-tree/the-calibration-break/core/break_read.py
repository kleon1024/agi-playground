"""The calibration break that moved the strategy, read from the recorded run.

Stage 05's run holds the sharpest result in the value-tree chapter: with
weights unchanged and click predictions inflated 1.6x, the honest ranking
and the miscalibrated ranking disagree — order changed with no product-
strategy change. This script reads the record and lays out the break and
the auction that follows it.

Input (recorded, unchanged): ../runs/2026-07-30-weight-sweep-and-auction.md

Run:
    uv run python core/break_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2]
        / "runs"
        / "2026-07-30-weight-sweep-and-auction.md"
    ).read_text()
    honest = re.search(r"honest ranking\s+(\[.*?\])", run)
    mis = re.search(r"miscalibrated ranking\s+(\[.*?\])", run)
    print("the calibration break, read from the recorded value-tree run:")
    if honest and mis:
        print(f"  honest ranking:       {honest.group(1)}")
        print(f"  miscalibrated ranking: {mis.group(1)}")
    auction = re.findall(
        r"trade_rate=([\d.]+): ([\w ]+?)(?:, |$)", run
    )
    if auction:
        print("\n  ad auction, explicit trade rate:")
        for rate, outcome in auction:
            print(f"    {rate}: {outcome.strip()}")
    print("\nreading: the same strategy, different calibration, different slate —")
    print("a miscalibrated probability is not a slightly-wrong number, it is a")
    print("different product decision, which is why stage 04's ECE is a gate.")


if __name__ == "__main__":
    main()
