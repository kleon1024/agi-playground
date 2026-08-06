"""The restatement gap, read from the recorded point-in-time check.

Stage 00's run holds the sharpest evidence in the market-data chapter: the
same fiscal period, two different reported values, filed a year apart. This
script reads the record and lays out the gap and what a naive join would
have silently used.

Input (recorded, unchanged): ../runs/2026-07-30-point-in-time-check.md

Run:
    uv run python core/gap_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2]
        / "runs"
        / "2026-07-30-point-in-time-check.md"
    ).read_text()
    first = re.search(r"first filed ([\d-]+) = ([\d,]+) \(10-K\)", run)
    latest = re.search(r"latest filed ([\d-]+) = ([\d,]+) \(10-K\)", run)
    naive = re.search(r"naive join keyed only on fiscal period [\d-]+: ([\d,]+)", run)
    pit = re.search(r"point-in-time value as of ([\d-]+): ([\d,]+)", run)
    div = re.search(r"dividends: (\d+)  splits: (\d+)", run)
    err = re.search(r"median rel error: ([\d.]+)  max rel error: ([\d.]+)", run)
    print("the restatement gap, read from the recorded point-in-time check:")
    if first and latest:
        print(f"  FY2015 first filed ({first.group(1)}): {first.group(2)}")
        print(f"  FY2015 latest filed ({latest.group(1)}): {latest.group(2)}")
    if naive and pit:
        print(f"  naive join would use: {naive.group(1)} (the restatement)")
        print(f"  point-in-time as of {pit.group(1)}: {pit.group(2)}")
    if div and err:
        print(f"  corporate-action reconstruction: {div.group(1)} dividends, "
              f"{div.group(2)} splits, rel error {err.group(1)}/{err.group(2)}")
    print("\nreading: the same period, two values, filed a year apart — a naive")
    print("join silently uses the restatement, which is the survivorship-adjacent")
    print("error the point-in-time join exists to prevent.")


if __name__ == "__main__":
    main()
