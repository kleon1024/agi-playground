"""The 34-second loss curve, read from the recorded run.

The first training loop's recorded run holds the train/val loss at every
250-iteration checkpoint from 0 to 2000. This script reads that record and
lays out the curve's two halves — the fast descent and the growing
train/val gap — so "the loop works" and "the loop is overfitting" are
read off the same table.

Input (recorded, unchanged): ../runs/2026-07-26-tiny-shakespeare.md

Run:
    uv run python core/curve_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2]
        / "runs"
        / "2026-07-26-tiny-shakespeare.md"
    ).read_text()
    rows = re.findall(
        r"iter\s+(\d+)\s+train\s+([\d.]+)\s+val\s+([\d.]+)", run
    )
    assert len(rows) >= 8, f"expected the checkpoint table, found {len(rows)} rows"
    print("the recorded 2000-iteration curve:")
    print(f"  {'iter':>5} {'train':>7} {'val':>7} {'gap':>7}")
    for it, tr, va in rows:
        print(f"  {it:>5} {float(tr):>7.3f} {float(va):>7.3f} "
              f"{float(va)-float(tr):>+7.3f}")
    first, last = rows[0], rows[-1]
    gap_first = float(first[2]) - float(first[1])
    gap_last = float(last[2]) - float(last[1])
    print(f"\nreading: the loop learns fast (val {float(first[2]):.3f} -> "
          f"{float(last[2]):.3f}) and then the gap grows (train {float(last[1]):.3f} "
          f"vs val {float(last[2]):.3f}) — the descent and the overfitting are "
          f"the same curve, read at different times.")
    print(f"gap at start {gap_first:+.3f}, gap at end {gap_last:+.3f}")


if __name__ == "__main__":
    main()
