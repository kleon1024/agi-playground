"""The dead expert, read from the recorded MoE routing run.

The MoE chapter's run measured six top-k/shared configurations on a toy
with a 4:1 pattern skew. The sharpest row is top-1 without a shared expert:
the routing counts [45, 0, 6, 149] show one expert never used and one
dominant. This script reads the recorded run and lays out the collapse and
what the load-balancing machinery exists to fight.

Input (recorded, unchanged): ../runs/2026-08-06-moe-routing.md

Run:
    uv run python core/dead_expert_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-08-06-moe-routing.md"
    ).read_text()
    rows = re.findall(
        r"\s+(\d)\s+(\w+)\s+([\d.]+)\s+([\d.]+)\s+([\w.]+)\s+(\[[\d,]+\])",
        run,
    )
    print("the recorded MoE routing sweep, read:")
    print("  top-k shared  accuracy  entropy  imbalance  counts")
    for top_k, shared, acc, ent, imb, counts in rows:
        print(f"  {top_k}     {shared:<6} {acc}   {ent}    "
              f"{imb:<6} {counts}")
    dead = re.search(r"Top-1 under the 4:1 skew produces a dead expert.*", run)
    if dead:
        print(f"\nreading: {dead.group(0)}")


if __name__ == "__main__":
    main()
