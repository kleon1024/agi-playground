"""The all-reduce that makes ranks agree, read from the recorded run.

The distributed-training chapter ran real DDP and ZeRO-1 collectives on
four CPU processes. Its recorded run holds the three numbers that make
data parallelism work: the pre-reduction gradient delta, the asserted zero
post-reduction divergence, and the optimizer-state-to-parameter ratio. This
script reads that record and lays out the mechanism.

Input (recorded, unchanged): ../runs/2026-07-27-cpu-simulation.md

Run:
    uv run python core/rank_agreement.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2]
        / "runs"
        / "2026-07-27-cpu-simulation.md"
    ).read_text()

    def grab(pattern: str, default: str = "") -> str:
        m = re.search(pattern, run)
        return m.group(1) if m else default

    delta = grab(r"local-vs-averaged gradient delta = ([\d.]+)")
    per_rank_params = grab(r"per-rank parameters\s+([\d.]+ [A-Za-z]+)")
    per_rank_state = grab(r"per-rank optimizer state\s+([\d.]+ [A-Za-z]+)")
    ratio = grab(r"ratio optimizer:params\s+([\d.]+x)")
    zero_state = grab(r"per-rank optimizer state\s+([\d.]+ [A-Za-z]+)\s+\(sharded /4\)")

    print("the recorded 4-rank DDP / ZeRO-1 run, read:")
    print(f"  pre-all-reduce gradient delta: {delta}")
    print("  post-all-reduce divergence: asserted zero across ranks")
    print(f"  DDP optimizer state: {per_rank_state} vs parameters {per_rank_params} "
          f"({ratio})")
    print(f"  ZeRO-1 optimizer state: {zero_state} (sharded /4)")
    print("\nreading: the delta is the whole point of DDP — ranks see different")
    print("data so their gradients differ, and the all-reduce is what makes")
    print("them identical again; the 2x optimizer ratio is why ZeRO exists.")


if __name__ == "__main__":
    main()
