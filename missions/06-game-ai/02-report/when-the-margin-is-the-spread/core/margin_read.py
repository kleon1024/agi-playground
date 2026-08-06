"""The margin-vs-spread arithmetic, read from the recorded outcome report.

Stage 02's report judged GRPO against both baselines. This script reads
the recorded outcome and lays out the margin-vs-spread comparison that
made the verdict honest.

Input (recorded, unchanged): ../runs/2026-07-31-outcome-report.md

Run:
    uv run python core/margin_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-07-31-outcome-report.md"
    ).read_text()
    print("mission 06 outcome report (recorded), read:")
    for row in re.findall(
        r"(random[^\n]*|greedy[^\n]*|VERDICT[^\n]*|NOT MET[^\n]*|MET[^\n]*|"
        r"below (?:the )?[^\n]*)", run
    ):
        print(f"  {row.strip()}")
    print("\nreading: the verdict is honest because the margin is compared")
    print("against the policy's own seed spread — a positive margin inside")
    print("the spread is a no-result, not a win.")


if __name__ == "__main__":
    main()
