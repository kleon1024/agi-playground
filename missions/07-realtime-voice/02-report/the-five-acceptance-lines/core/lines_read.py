"""The five acceptance lines, read from the recorded outcome report.

Stage 02's MET verdict rests on five acceptance lines independently. This
script reads the recorded report and lays out each line and the load-
bearing one.

Input (recorded, unchanged): ../runs/2026-07-31-outcome-report.md

Run:
    uv run python core/lines_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-07-31-outcome-report.md"
    ).read_text()
    print("mission 07 acceptance lines (recorded), read:")
    for row in re.findall(
        r"(codec \(stage 00[^\n]*|LM completion \(stage 01[^\n]*|"
        r"oracle \(stage 01[^\n]*|quality gap: ZERO[^\n]*|"
        r"no change was required[^\n]*|VERDICT: MET)", run
    ):
        print(f"  {row.strip()}")
    print("\nreading: MET depends on all five lines independently — the codec")
    print("and LM must each beat both baselines, the gap must be a true zero,")
    print("the latency must be measured at two scales, and no reused serving")
    print("code may change. Flip any one and the verdict changes.")


if __name__ == "__main__":
    main()
