"""The real-time bid, read: the exchange has 100 ms.

Stage 29 runs the RTB pipeline. This script reads a bid request's latency
budget split across the pipeline stages.

Run:
    uv run python core/rtb_latency.py
"""

from __future__ import annotations


def main() -> None:
    budget_ms = 100.0
    stages = {
        "request parse": 5.0,
        "user profile lookup": 20.0,
        "context features": 10.0,
        "model inference": 25.0,
        "bid decision": 15.0,
        "response send": 5.0,
    }
    total = sum(stages.values())
    print("RTB budget, read (100 ms):")
    for name, ms in stages.items():
        print(f"  {name}: {ms:.0f} ms")
    print(f"  total: {total:.0f} ms, margin {budget_ms - total:.0f} ms")
    print("\nreading: five stages consume 80 ms, leaving 20 ms of margin.")
    print("Every stage is a latency source and a potential timeout — the")
    print("pipeline's p95 is the sum of its worst stages, which is why RTB")
    print("engineering is mostly about keeping the tail inside the budget.")


if __name__ == "__main__":
    main()
