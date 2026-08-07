"""The public-set control, read from the recorded outcome report.

Stage 05's bullet-4 finding is that the public set exists and is reported
separately from the private set, never pooled. This script reads the
recorded outcome report and lays out the two sets' resolve numbers.

Input (recorded, unchanged): ../runs/2026-08-01-outcome-report.txt

Run:
    uv run python core/public_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    txt = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-08-01-outcome-report.txt"
    ).read_text()
    print("public vs private sets (recorded outcome report), read:")
    for row in re.findall(
        r"(private \(harness[^\n]*|public \(harness[^\n]*)", txt
    ):
        print(f"  {row}")
    pooled = re.search(r"(reported side by side[^\n]*)", txt)
    if pooled:
        print(f"  {pooled.group(1)}")
    print("\nreading: the public set is the contamination-prone counterpart —")
    print("its 6/6 says nothing about the private 18/18, and pooling them")
    print("would hide which set each number belongs to.")


if __name__ == "__main__":
    main()
