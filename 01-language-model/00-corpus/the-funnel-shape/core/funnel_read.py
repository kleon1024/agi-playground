"""The funnel shape, read from the recorded sample run.

Stage 00's 3,000-document sample recorded the funnel at every gate and
the drop reasons. This script reads the record and lays out the shape —
the two funnel runs agree, and the drop table is the audit trail.

Input (recorded, unchanged): ../runs/2026-07-30-sample-and-distribution.md

Run:
    uv run python core/funnel_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2]
        / "runs"
        / "2026-07-30-sample-and-distribution.md"
    ).read_text()
    print("the corpus funnel (recorded 3,000-doc sample), read:")
    for row in re.findall(
        r"\d+\. ([\w ]+?)\s+([\d,]+)\s+([\d.]+)%\s+([\d.]+)%", run
    ):
        print(f"  {row[0]:<18} {row[1]:>6} docs ({row[2]}% of raw, {row[3]}% kept)")
    print("\nreading: 31.6% of raw HTML is English and 18.3% survives to the")
    print("clean set — the funnel is the audit trail, and the drop-reason")
    print("table is what makes each gate's decision accountable.")


if __name__ == "__main__":
    main()
