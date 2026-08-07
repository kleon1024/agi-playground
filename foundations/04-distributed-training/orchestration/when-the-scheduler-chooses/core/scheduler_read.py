"""The scheduler that chooses whose work waits, read from the recorded JSON.

The orchestration chapter compared FIFO and priority scheduling on two
slots. The recorded JSON holds the per-policy makespan and the high/low-
priority waits. This script reads it and lays out the reading: makespan
is essentially unchanged — what the scheduler changes is whose work waits.

Input (recorded, unchanged): ../runs/scheduler-result.json

Run:
    uv run python core/scheduler_read.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path


def main() -> None:
    with open(
        Path(__file__).resolve().parents[2] / "runs" / "scheduler-result.json"
    ) as fh:
        d = json.load(fh)
    print("FIFO vs priority (recorded), read:")
    for name in ("fifo", "priority"):
        p = d[name]
        makespans = [t["makespan_s"] for t in p["trials"]]
        hi = [t["high_priority_mean_wait_s"] for t in p["trials"]]
        lo = [t["low_priority_mean_wait_s"] for t in p["trials"]]
        print(
            f"  {name:<9} makespan {statistics.fmean(makespans):.4f}s "
            f"| hi-priority wait {statistics.fmean(hi):.4f}s "
            f"| lo-priority wait {statistics.fmean(lo):.4f}s"
        )
    print("\nreading: the scheduler does not do more work — it decides whose")
    print("work happens first. Makespan barely moves; the wait distribution")
    print("is the entire difference.")


if __name__ == "__main__":
    main()
