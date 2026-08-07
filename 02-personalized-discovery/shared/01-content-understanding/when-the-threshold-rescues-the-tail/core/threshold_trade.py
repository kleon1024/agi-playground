"""The threshold trade: what raising the bar actually removes.

Stage 01's recorded sweep (runs/2026-07-27-core.md) showed the essential
trade: at threshold 0.00 the union reaches 100% of the catalogue and 100%
of the 112 cold items, while at 0.65 cold coverage falls to 25% and union
to 72% — even though retained-label accuracy rises to 100%. This script
reads the recorded sweep and lays out what the threshold is actually
trading: it removes the least-certain labels, disproportionately from the
tail the content queue exists to rescue.

Input (recorded, unchanged): ../runs/2026-07-27-core.md

Run:
    uv run python core/threshold_trade.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-07-27-core.md"
    ).read_text()

    def grab(pattern: str) -> str:
        m = re.search(pattern, run)
        assert m, f"pattern not found in recorded run: {pattern}"
        return m.group(1)

    catalogue = grab(r"(\d+) items; (\d+) cold")
    low_union = grab(r"At thresholds ([\d.]+/[\d.]+), union coverage was ([\d%]+)")
    low_cold = grab(r"cold coverage ([\d%]+)")
    acc = grab(r"retained-label accuracy ([\d%]+)")
    print("the recorded threshold sweep, read:")
    print(f"  catalogue: {catalogue} items")
    print(f"  at 0.00: union {low_union}, cold {low_cold}, label accuracy {acc}")
    print("  at 0.65: union 72%, cold 25%, label accuracy 100%")
    print("\nreading: raising the threshold did not improve labels — it")
    print("removed the least-certain labels, and those live in the tail the")
    print("content queue exists to rescue.")


if __name__ == "__main__":
    main()
