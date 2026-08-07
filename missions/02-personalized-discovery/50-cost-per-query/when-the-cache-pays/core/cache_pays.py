"""Cache pays, read: the served query is cheaper than the computed
one.

Stage 50 detour: a hot item's slate is computed once and served many
times. The cache turns a per-query cost into a per-unique-query cost;
the hit rate decides how much of the budget it saves.

Run:
    uv run python core/cache_pays.py
"""

from __future__ import annotations

FULL_COST = 4.0  # cost units of a computed query (stage 50)


def main() -> None:
    print("cache pays, read (cost units per served query, full cost 4.0):")
    for hit_rate in (0.0, 0.5, 0.9, 0.99):
        per_served = (1.0 - hit_rate) * FULL_COST + hit_rate * 0.05
        print(f"  hit rate {hit_rate:.0%}: {per_served:.2f} units per served query")
    print("\nreading: at 90% hits the per-served cost drops to a tenth")
    print("of the full path. The cache is not free - it trades freshness")
    print("for cost, and a stale cached slate is the same trade as a")
    print("stale model. The hit-rate curve is where the cache decision")
    print("is measured.")


if __name__ == "__main__":
    main()
