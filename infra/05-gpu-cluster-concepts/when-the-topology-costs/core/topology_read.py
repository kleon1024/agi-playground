"""The coordination tax, read from the recorded all-reduce timings.

The GPU-cluster chapter timed all-reduce over 200 iterations at world
sizes 2, 4, 8 with a fixed 4 MB tensor. This script reads the recorded run
and lays out the pattern: the mean per-call wall-clock grows with world
size even though the tensor never changes — the tax is coordination, not
data.

Input (recorded, unchanged): ../runs/2026-08-01-topology-timing.md

Run:
    uv run python core/topology_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-08-01-topology-timing.md"
    ).read_text()
    rows = re.findall(
        r"world_size=\s*(\d+)\s+tensor=([\d.]+)MB\s+mean all_reduce wall-clock = ([\d.]+) ms/call",
        run,
    )
    print("all-reduce over 200 iterations, 4 MB tensor (recorded), read:")
    for world, mb, ms in rows:
        print(f"  world {world:>2}: {float(ms):.2f} ms/call  (tensor {mb} MB, fixed)")
    if len(rows) >= 3:
        base = float(rows[0][2])
        print(f"\n  growth vs world 2: x{float(rows[1][2])/base:.2f} (world 4), "
              f"x{float(rows[2][2])/base:.2f} (world 8)")
    print("\nreading: the tensor never changes, so the growth is coordination")
    print("overhead — more ranks to synchronize, more hops — which is why")
    print("the cluster's wiring decides the parallelism strategy.")


if __name__ == "__main__":
    main()
