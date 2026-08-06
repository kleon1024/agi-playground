"""The search log, read from the recorded signal-search run.

Stage 01's run logged every candidate variant and then permuted the
forward returns to price the search itself. This script reads the recorded
run and lays out the two numbers that decide whether the best signal is
real: the best in-sample IC and the permutation p-value.

Input (recorded, unchanged): ../runs/2026-07-27-core-signal-search.md

Run:
    uv run python core/search_log_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2]
        / "runs"
        / "2026-07-27-core-signal-search.md"
    ).read_text()
    variants = re.search(r"logged (\d+) real\s+candidate variants", run, re.DOTALL)
    best = re.search(r"best in-sample IC was ([\d.]+) for ([\w-]+) with ([\d-]+)-month", run, re.DOTALL)
    perm = re.search(r"permutation p-value of ([\d.]+)", run, re.DOTALL)
    matched = re.search(r"([\d]+) of 300 null searches matched or exceeded", run, re.DOTALL)
    print("the signal search, read from the recorded run:")
    if variants:
        print(f"  candidates logged: {variants.group(1)}")
    if best:
        print(f"  best in-sample IC: {best.group(1)} ({best.group(2)}, "
              f"{best.group(3)} month)")
    if matched and perm:
        print(f"  null searches matching the winner: {matched.group(1)}/300")
        print(f"  permutation p-value: {perm.group(1)}")
    print("\nreading: the winner is real only if it survives the search itself —")
    print("95/300 null searches matched it, so p=0.317, which is not a result.")


if __name__ == "__main__":
    main()
