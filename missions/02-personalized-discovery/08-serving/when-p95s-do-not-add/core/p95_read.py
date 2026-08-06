"""Why stage p95s do not add, read from the recorded latency run.

Stage 08's run compared serial and parallel funnel latency and tested the
"add the p95s" rule. The recorded numbers show the trap: summing per-stage
p95 gives 54.74ms, above the measured end-to-end p95 of 49.31ms. This
script reads the record and lays out the composition rules.

Input (recorded, unchanged): ../runs/2026-07-27-core.md

Run:
    uv run python core/p95_read.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-07-27-core.md"
    ).read_text()
    print("latency composition (recorded), read:")
    for row in re.findall(
        r"(parallel no-cache mean/p95 [\d.]+/[\d.]+ms; serial [\d.]+/[\d.]+ms;"
        r" 80% configured cache observed [\d.]+ and mean/p95 [\d.]+/[\d.]+ms."
        r" Parallel p95-sum estimate was [\d.]+ms vs measured [\d.]+ms)",
        run,
    ):
        print(f"  {row}")
    print("\nreading: means add for the serial path; tail percentiles do not.")
    print("A request is slow only when its stages align in the tail, and the")
    print("p95-sum (54.74) over the measured p95 (49.31) is the trap. The")
    print("cache is the third row: p95 collapses 49.31 -> 34.52ms.")


if __name__ == "__main__":
    main()
