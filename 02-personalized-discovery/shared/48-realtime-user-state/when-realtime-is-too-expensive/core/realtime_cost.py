"""Realtime is too expensive, read: every live feature is a millisecond
on the critical path.

Stage 48 detour: realtime features must be computed per request.
Each one adds latency to the p95, and the deadline is fixed. At some
count the realtime state stops paying for itself - the hybrid keeps
the cheap features live and demotes the rest to a batch refresh.

Run:
    uv run python core/realtime_cost.py
"""

from __future__ import annotations

DEADLINE = 100.0
BASE_P95 = 38.0
MS_PER_FEATURE = 4.0


def main() -> None:
    print("realtime is too expensive, read (p95 per request, deadline 100ms):")
    for n_features in (0, 5, 10, 20):
        p95 = BASE_P95 + n_features * MS_PER_FEATURE
        status = "ok" if p95 <= DEADLINE else "over"
        print(f"  {n_features:>2} realtime features: p95 {p95:.0f}ms ({status})")
    print("\nreading: the batch path alone sits at 38ms. Ten realtime")
    print("features push the p95 to 78ms - still inside the deadline;")
    print("twenty blow through it. Every feature added to the request")
    print("path is a latency budget spent, and the ones whose signal")
    print("does not change minute to minute belong in the batch path,")
    print("not on the critical one.")


if __name__ == "__main__":
    main()
