"""The quadratic verification tail, read from the recorded scaling run.

The dedup chapter ran MinHash hashing and LSH bucket verification at
corpus sizes 1k, 4k, 16k, 48k. This script reads the recorded run and lays
out the pattern: hashing grows linearly with n, verification grows
quadratically (x16 for x4 corpus) because it checks pairs, not documents.

Input (recorded, unchanged): ../runs/2026-08-01-dedup-scaling.md

Run:
    uv run python core/dedup_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-08-01-dedup-scaling.md"
    ).read_text()
    print("MinHash vs LSH verification by corpus size (recorded), read:")
    for row in re.findall(
        r"\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s+(\d+)\s+(\d+)",
        run,
    ):
        n, hash_s, verify_s, pairs, near = (
            row[0],
            row[1],
            row[3],
            row[4],
            row[6],
        )
        print(
            f"  n={int(n):>6}  hash {float(hash_s):>8.2f}s  "
            f"verify {float(verify_s):>8.2f}s  pairs {int(pairs):>9}  "
            f"near-dupes {int(near):>9}"
        )
    for row in re.findall(
        r"n x4\.0: hash_time x([\d.]+), verify_time x([\d.]+)",
        run,
    ):
        print(f"  n x4.0 -> hash_time x{row[0]}, verify_time x{row[1]}")
    print("\nreading: hashing is per-document (linear), verification is")
    print("per-pair (quadratic) — the LSH trade is accepting a bounded")
    print("false-negative risk to keep the verify step from exploding.")


if __name__ == "__main__":
    main()
