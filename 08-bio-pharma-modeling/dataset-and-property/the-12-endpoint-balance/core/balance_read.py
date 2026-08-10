"""The 12-endpoint balance table, read from the recorded dataset run.

Stage 00 computed every Tox21 endpoint's label balance before choosing
SR-MMP. This script reads the recorded table and lays out why the choice
was made from balance, not convenience.

Input (recorded, unchanged): ../runs/2026-08-01-dataset-and-split.md

Run:
    uv run python core/balance_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2]
        / "runs"
        / "2026-08-01-dataset-and-split.md"
    ).read_text()
    print("Tox21 endpoint balance (recorded), read:")
    for row in re.findall(
        r"\| \*{0,2}([\w-]+)\*{0,2} \| \*{0,2}(\d+)\*{0,2} \| \*{0,2}(\d+)\*{0,2} \| \*{0,2}([\d.]+)%\*{0,2} \|", run
    ):
        print(f"  {row[0]:<14} labeled {row[1]:>6} positive {row[2]:>5} "
              f"({row[3]}%)")
    print("\nreading: SR-MMP (15.8%) is the best-balanced endpoint with a")
    print("single statable mechanism — the choice is made from balance and")
    print("assay semantics before any model sees the data, per the guardrail")
    print("against choosing after seeing which endpoint flatters a number.")


if __name__ == "__main__":
    main()
