"""The heavy tail that waits, read from the recorded scheduling JSON.

The rollout-concurrency chapter fed the same 40-trajectory list to
lockstep and async policies at 2, 4, 8 workers. This script reads the
recorded JSON and lays out the reading: async wins because workers do not
wait on the slowest rollout — the heavy-tailed episode lengths are exactly
where the difference lives.

Input (recorded, unchanged): ../runs/rollout-scheduling-result.json

Run:
    uv run python core/rollout_read.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    with open(
        Path(__file__).resolve().parents[2] / "runs" / "rollout-scheduling-result.json"
    ) as fh:
        d = json.load(fh)
    print("lockstep vs async rollout scheduling (recorded), read:")
    for key in ("workers_2", "workers_4", "workers_8"):
        w = d[key]
        lock = w["lockstep"]["makespan_s"]["mean"]
        async_ = w["async"]["makespan_s"]["mean"]
        print(
            f"  {key.replace('_', ' ')}: lockstep {lock:.4f}s  async {async_:.4f}s  "
            f"speedup {lock/async_:.2f}x"
        )
    print("\nreading: the same trajectory list, the only difference the")
    print("policy — async wins because a finished worker grabs the next")
    print("rollout instead of waiting on the long tail.")


if __name__ == "__main__":
    main()
