"""Peak arrives, read: a ten-minute spike is a capacity decision, not
a load average.

Stage 49 detour: traffic is provisioned for the average hour, and the
spike is several times it. The queue grows, latency crosses the
deadline, and the share of dropped queries is the real cost of the
peak.

Run:
    uv run python core/peak_arrives.py
"""

from __future__ import annotations

import random


def simulate(base_rate: float, peak_multiplier: float, seed: int = 6) -> dict[str, float]:
    rng = random.Random(seed)
    peak_rate = base_rate * peak_multiplier
    interval = 1000.0 / peak_rate
    latencies: list[float] = []
    busy_until = 0.0
    for i in range(20_000):
        arrival = i * interval
        service = 150.0 if rng.random() < 0.05 else 10.0
        start = max(arrival, busy_until)
        latencies.append(start + service - arrival)
        busy_until = start + service
    over = sum(1 for lat in latencies if lat > 100.0) / len(latencies)
    latencies.sort()
    return {
        "p50": latencies[len(latencies) // 2],
        "p99": latencies[int(len(latencies) * 0.99)],
        "over": over,
    }


def main() -> None:
    base = 30.0  # a quiet-hour rate, well under capacity
    print("peak arrives, read (base 30 req/s, service mean 17ms):")
    for multiplier in (1.0, 2.0, 5.0):
        stats = simulate(base, multiplier)
        print(f"  {multiplier:.0f}x peak ({base * multiplier:.0f} req/s): "
              f"p50 {stats['p50']:.0f}ms, p99 {stats['p99']:.0f}ms, "
              f"over 100ms {stats['over']:.1%}")
    print("\nreading: at 1x the service is comfortable; at 2x the tail")
    print("crosses the deadline; at 5x most queries miss it. The peak")
    print("does not raise the average - it floods the queue. Capacity")
    print("for the peak is bought with idle servers the rest of the")
    print("day, or paid for with dropped queries at the peak.")


if __name__ == "__main__":
    main()
