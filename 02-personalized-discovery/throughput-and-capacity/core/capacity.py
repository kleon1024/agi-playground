"""Throughput and capacity, read: the tail decides how many servers
you need.

Stage 49 introduces capacity planning. A query takes a service time;
requests arrive at a rate; the queue grows when arrival rate nears
service capacity. Sizing to the average latency misses the tail - a
small share of slow queries is what pushes latency past the deadline.

Run:
    uv run python core/capacity.py
    uv run python core/capacity.py --emit-log /tmp/capacity-envelope.json

The `--emit-log` flag writes per-load latency stats plus the full scan
so the production path in `prod/capacity_audit.py` can answer the
case-finding question of the stage: capacity is found by load-testing
with a deadline, not by the mean service time.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

DEADLINE_MS = 100.0


def service_time(rng: random.Random) -> float:
    """10ms mean, with 5% of queries at 150ms."""
    return 150.0 if rng.random() < 0.05 else 10.0


def simulate(arrivals_per_second: float, seed: int = 3) -> dict[str, object]:
    """Single FIFO server at a fixed arrival rate."""
    rng = random.Random(seed)
    interval = 1000.0 / arrivals_per_second
    latencies: list[float] = []
    busy_until = 0.0
    for i in range(10_000):
        arrival = i * interval
        service = service_time(rng)
        start = max(arrival, busy_until)
        latencies.append(start + service - arrival)
        busy_until = start + service
    latencies.sort()
    over = sum(1 for lat in latencies if lat > DEADLINE_MS) / len(latencies)
    # The service mean: 0.95 * 10ms + 0.05 * 150ms.
    mean_service = 0.95 * 10.0 + 0.05 * 150.0
    return {
        "p50": latencies[len(latencies) // 2],
        "p95": latencies[int(len(latencies) * 0.95)],
        "p99": latencies[int(len(latencies) * 0.99)],
        "over_deadline": over,
        "utilization": arrivals_per_second * mean_service / 1000.0,
    }


SCAN_LOADS = [20, 30, 40, 45, 50, 55, 60]


def scan() -> list[dict[str, object]]:
    return [
        {"load": load, **simulate(load)}  # type: ignore[arg-type]
        for load in SCAN_LOADS
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-log", help="write the per-load stats as JSON")
    args = parser.parse_args()
    print("throughput and capacity, read (10ms service, 5% at 150ms):")
    for rate in (20, 40, 55):
        stats = simulate(rate)
        print(f"  {rate} req/s: p50 {stats['p50']:.0f}ms, "
              f"p95 {stats['p95']:.0f}ms, p99 {stats['p99']:.0f}ms, "
              f"over 100ms {stats['over_deadline']:.1%}")
    loads = scan()
    print("\ncapacity scan (deadline 100ms):")
    print(f"  {'load':>4} {'util':>5}  {'p50':>5} {'p95':>5} {'p99':>5} "
          f"{'over 100ms':>10}")
    for row in loads:
        print(
            f"  {row['load']:>4} {row['utilization']:>5.0%}  "
            f"{row['p50']:.0f} {row['p95']:.0f} {row['p99']:.0f} "
            f"{row['over_deadline']:>10.1%}"
        )
    mean_service = 0.95 * 10.0 + 0.05 * 150.0
    mean_capacity = 1000.0 / mean_service
    print(f"\n  mean-service capacity (divergence load): "
          f"{mean_capacity:.0f} req/s.")
    print("\nreading: service averages 17ms, so the naive capacity is")
    print("roughly 59 req/s. The tail grows first: at 55 req/s the p99")
    print("is many times the p50 and a real share of queries miss the")
    print("100ms deadline. Capacity planning is throughput x deadline,")
    print("not throughput x average latency.")
    if args.emit_log:
        Path(args.emit_log).write_text(
            json.dumps(
                {
                    "deadline_ms": DEADLINE_MS,
                    "mean_service_ms": mean_service,
                    "tail_service_ms": 150.0,
                    "loads": loads,
                }
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
