"""Throughput and capacity, read: the tail decides how many servers
you need.

Stage 49 introduces capacity planning. A query takes a service time;
requests arrive at a rate; the queue grows when arrival rate nears
service capacity. Sizing to the average latency misses the tail - a
small share of slow queries is what pushes latency past the deadline.

Run:
    uv run python core/capacity.py
"""

from __future__ import annotations

import random


def simulate(arrivals_per_second: float, seed: int = 3) -> dict[str, float]:
    """Single FIFO server. Service time: 10ms, with 5% at 150ms."""
    rng = random.Random(seed)
    interval = 1000.0 / arrivals_per_second
    latencies: list[float] = []
    busy_until = 0.0
    for i in range(10_000):
        arrival = i * interval
        if rng.random() < 0.05:
            service = 150.0
        else:
            service = 10.0
        start = max(arrival, busy_until)
        latencies.append(start + service - arrival)
        busy_until = start + service
    latencies.sort()
    over = sum(1 for lat in latencies if lat > 100.0) / len(latencies)
    return {
        "p50": latencies[len(latencies) // 2],
        "p95": latencies[int(len(latencies) * 0.95)],
        "p99": latencies[int(len(latencies) * 0.99)],
        "over_deadline": over,
    }


def main() -> None:
    print("throughput and capacity, read (10ms service, 5% at 150ms):")
    for rate in (20, 40, 55):
        stats = simulate(rate)
        print(f"  {rate} req/s: p50 {stats['p50']:.0f}ms, "
              f"p95 {stats['p95']:.0f}ms, p99 {stats['p99']:.0f}ms, "
              f"over 100ms {stats['over_deadline']:.1%}")
    print("\nreading: service averages 17ms, so the naive capacity is")
    print("roughly 59 req/s. The tail grows first: at 55 req/s the p99")
    print("is many times the p50 and a real share of queries miss the")
    print("100ms deadline. Capacity planning is throughput x deadline,")
    print("not throughput x average latency.")


if __name__ == "__main__":
    main()
