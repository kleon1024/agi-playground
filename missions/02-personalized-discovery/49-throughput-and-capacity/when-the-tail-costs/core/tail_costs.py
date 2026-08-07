"""Tail costs, read: sizing to the average is sizing to a fiction.

Stage 49 detour: mean service time suggests one capacity; the tail
demands another. A server provisioned on the mean drops a real share
of queries past the deadline, and the share is the capacity cost of
the tail.

Run:
    uv run python core/tail_costs.py
"""

from __future__ import annotations

import random


def simulate(arrivals_per_second: float, seed: int = 4) -> dict[str, float]:
    rng = random.Random(seed)
    interval = 1000.0 / arrivals_per_second
    latencies: list[float] = []
    busy_until = 0.0
    for i in range(20_000):
        arrival = i * interval
        service = 150.0 if rng.random() < 0.05 else 10.0
        start = max(arrival, busy_until)
        latencies.append(start + service - arrival)
        busy_until = start + service
    latencies.sort()
    over = sum(1 for lat in latencies if lat > 100.0) / len(latencies)
    return {
        "p50": latencies[len(latencies) // 2],
        "p99": latencies[int(len(latencies) * 0.99)],
        "over": over,
    }


def main() -> None:
    mean_service = 0.95 * 10.0 + 0.05 * 150.0
    mean_capacity = 1000.0 / mean_service
    print("tail costs, read (mean service 17ms -> mean capacity "
          f"{mean_capacity:.0f} req/s):")
    for load in (0.5, 0.8, 1.0):
        rate = mean_capacity * load
        stats = simulate(rate)
        print(f"  {load:.0%} of mean capacity ({rate:.0f} req/s): "
              f"p50 {stats['p50']:.0f}ms, p99 {stats['p99']:.0f}ms, "
              f"over 100ms {stats['over']:.1%}")
    print("\nreading: at the capacity the mean suggests, a tenth of")
    print("queries miss the deadline; at half that load the tail still")
    print("dominates the p99. Provisioning on the mean is how a")
    print("service 'at capacity' spends its budget failing the slow")
    print("queries the mean never saw.")


if __name__ == "__main__":
    main()
