"""When ring beats star, read from the recorded allreduce sweep.

The networking chapter ran star and ring allreduce at world sizes 2, 4, 8
and payloads 1, 8, 32 MB over localhost IPC. This script reads the recorded
run and lays out the pattern the 9-combination sweep shows: ring moves half
the bytes per rank and wins on wall-clock at every cell, by more at larger
payload.

Input (recorded, unchanged): ../runs/2026-08-01-star-vs-ring.md

Run:
    uv run python core/ring_vs_star_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-08-01-star-vs-ring.md"
    ).read_text()
    print("star vs ring allreduce (recorded sweep), read:")
    print(f"  {'world':>5} {'payload':>8} {'star_s':>8} {'ring_s':>8} "
          f"{'ring/star time':>13} {'star bytes/rank':>15} {'ring bytes/rank':>15}")
    for row in re.findall(
        r"\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s+(\d+)\s+True",
        run,
    ):
        world, payload, star_s, ring_s, star_b, ring_b = row
        print(
            f"  {world:>5} {payload:>8} {float(star_s):>8.4f} {float(ring_s):>8.4f} "
            f"{float(ring_s)/float(star_s):>12.2f} {int(star_b):>15} {int(ring_b):>15}"
        )
    print("\nreading: ring halves the bytes each rank moves and wins time at")
    print("every cell; the advantage grows with payload because bandwidth, not")
    print("latency, is what the topology trades.")


if __name__ == "__main__":
    main()
