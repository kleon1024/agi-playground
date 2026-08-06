"""The step the mean hides, read from the recorded histogram.

The observability chapter instrumented a training loop and recorded the
per-step time distribution (p50, p95, min, max, mean). This script reads
the recorded JSON and lays out the reading: the mean step time is close to
p50, and the max step is the tail that a mean hides.

Input (recorded, unchanged): ../runs/instrumented-train-result.json

Run:
    uv run python core/tail_read.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    with open(
        Path(__file__).resolve().parents[2] / "runs" / "instrumented-train-result.json"
    ) as fh:
        d = json.load(fh)
    s = d["step_time_s"]
    print("instrumented training (recorded), read:")
    print(f"  steps={d['counters']['steps']} tokens={d['counters']['tokens']}")
    print(f"  step time: p50 {s['p50']*1000:.2f}ms  p95 {s['p95']*1000:.2f}ms  "
          f"mean {s['mean']*1000:.2f}ms  min {s['min']*1000:.2f}ms  "
          f"max {s['max']*1000:.2f}ms")
    print(f"  max/mean ratio: {s['max']/s['mean']:.2f}x")
    print("\nreading: the mean (18.7ms) hides the step that took 29.9ms — a")
    print("latency budget set from the mean misses the tail that becomes a")
    print("timeout, which is why p95 exists as a metric.")


if __name__ == "__main__":
    main()
