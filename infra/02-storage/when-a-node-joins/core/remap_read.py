"""The remap that adding a node costs, read from the recorded shard run.

The storage chapter ran modulo and consistent-hash placement for 2,000 keys
over 4 nodes, then added a 5th and measured the real disk remap. This
script reads the recorded run and lays out the 0.802-vs-0.180 comparison
against the ideal 0.200 share a new node should take.

Input (recorded, unchanged): ../runs/2026-08-01-modulo-vs-consistent-hashing.md

Run:
    uv run python core/remap_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2]
        / "runs"
        / "2026-08-01-modulo-vs-consistent-hashing.md"
    ).read_text()
    print("modulo vs consistent-hash, read from the recorded run:")
    for row in re.findall(
        r"\s+(modulo|consistent)\s+([\d.]+)\s+([\d.]+)\n", run
    ):
        print(f"  {row[0]:<11} remap {float(row[1]):.3f} vs ideal {float(row[2]):.3f}")
    moved = re.findall(
        r"\s+(modulo|consistent)\s+(\d+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)",
        run,
    )
    if moved:
        print("\nreal disk remap (write under old placement, move to new):")
        for scheme, keys, bytes_, elapsed, mbs in moved:
            print(f"  {scheme:<11} moved {keys} keys, {int(bytes_)} bytes, "
                  f"{float(elapsed):.4f}s, {float(mbs):.0f} MB/s")
    print("\nreading: modulo remaps ~4x the ideal share because one node's")
    print("change rehashes every key; consistent hashing moves only the keys")
    print("the new node actually takes.")


if __name__ == "__main__":
    main()
