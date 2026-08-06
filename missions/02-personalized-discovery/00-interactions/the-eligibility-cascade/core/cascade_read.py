"""The eligibility cascade, read from the recorded MovieLens run.

Stage 00's filter drops rows iteratively: removing a sparse item can push a
user below their own threshold, which can push another item below its own.
The recorded run holds the per-user consequence of that cascade. This
script reads the record and lays out what the loop actually removed and
which users the cascade caught.

Input (recorded, unchanged): ../runs/2026-07-30-movielens-split.md

Run:
    uv run python core/cascade_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2]
        / "runs"
        / "2026-07-30-movielens-split.md"
    ).read_text()
    dropped = re.search(r"below min-interactions, dropped (\d+)", run)
    sparse = re.search(r"([\d,]+) of ([\d,]+) movies have fewer than 5 ratings", run)
    users = re.findall(r"user (\d+) \(([\d]+) -> ([\d]+)\)", run)
    print("the eligibility cascade, read from the recorded MovieLens run:")
    print(f"  rows dropped by the iterative filter: {dropped.group(1) if dropped else '?'}")
    if sparse:
        print(f"  sparse movies (fewer than 5 ratings): {sparse.group(1)} of {sparse.group(2)}")
    if users:
        print("  users the cascade caught (fell below the floor after item drops):")
        for uid, before, after in users:
            print(f"    user {uid}: {before} -> {after}")
    print("\nreading: eligibility is per item AND per user, and the two interact —")
    print("the loop exists because one pass is not enough, and the users above")
    print("are the proof the cascade is real, not a rounding detail.")


if __name__ == "__main__":
    main()
