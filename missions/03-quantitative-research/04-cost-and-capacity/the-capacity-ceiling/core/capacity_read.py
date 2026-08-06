"""The capacity ceiling, read from the recorded cost-and-capacity run.

Stage 04's run measured ADV and volatility, then priced a 10m book against
assumed costs. The recorded numbers hold the two capacity thresholds: the
peak book and the total-return breakeven. This script reads the record and
lays out where the book stops.

Input (recorded, unchanged): ../runs/2026-07-27-cost-capacity.md

Run:
    uv run python core/capacity_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-07-27-cost-capacity.md"
    ).read_text()
    print("cost and capacity (recorded), read:")
    for row in re.findall(
        r"(ADV USD [\d,]+|daily volatility [\d.]+%|at a USD 10m book, [\d.]+% "
        r"participation and [\d.]+% annual cost|discrete-sweep peak USD [\d,]+|"
        r"total-return breakeven USD [\d,]+)",
        run,
    ):
        print(f"  {row}")
    print("\nreading: the book stops where costs eat the edge — participation")
    print("caps the book by liquidity, breakeven caps it by cost, and both are")
    print("computed from measured ADV and volatility with declared assumptions.")


if __name__ == "__main__":
    main()
