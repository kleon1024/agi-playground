"""Tail misses, read: the cache concentrates on the head.

Stage 50 detour: a cache changes the cost arithmetic, but only for the
queries that repeat. Query frequency is heavy-tailed: a few distinct
queries own most of the traffic, and the long tail of unique queries
never repeats, so it never hits. The cache discounts the head and
leaves the tail paying the full cascade cost - which is where the
per-query budget is worst.

Run:
    uv run python core/tail_misses.py
"""

from __future__ import annotations

# Full cascade cost and the cost of a served cache hit.
MISS_COST = 4.0
HIT_COST = 0.05

# Query-frequency segments: share of traffic, cache hit rate.
SEGMENTS = [
    {"name": "head", "traffic": 0.40, "hit": 0.95},
    {"name": "mid", "traffic": 0.30, "hit": 0.50},
    {"name": "tail", "traffic": 0.30, "hit": 0.00},
]


def effective_cost(hit_rate: float) -> float:
    return hit_rate * HIT_COST + (1.0 - hit_rate) * MISS_COST


def main() -> None:
    print("tail misses, read (cascade 4.0 units; cache hit 0.05 units):")
    print(f"  {'segment':<6} {'traffic':>8} {'hit rate':>9} "
          f"{'cost/query':>11}")
    blended = 0.0
    overall_hit = 0.0
    for segment in SEGMENTS:
        cost = effective_cost(segment["hit"])
        blended += segment["traffic"] * cost
        overall_hit += segment["traffic"] * segment["hit"]
        print(
            f"  {segment['name']:<6} {segment['traffic']:>8.0%} "
            f"{segment['hit']:>9.0%} {cost:>11.2f}"
        )
    print(f"  {'blended':<6} {1.0:>8.0%} {overall_hit:>9.0%} {blended:>11.2f}")
    print(f"\n  without cache: 4.00 units/query; with cache: {blended:.2f} "
          f"units/query.")
    print("\nreading: the cache discounts the head and leaves the tail")
    print("paying the full 4.0 - unique queries never repeat, so they")
    print("never hit. The blended number (1.91) hides that 30% of")
    print("traffic still pays the full cascade. The tail is also where")
    print("recall dominates at scale (the stage's audit): cold queries")
    print("are exactly the recall-miss queries. A cache is a head")
    print("discount, not a capacity plan - when personalization makes")
    print("more of the traffic unique, the savings shrink with it.")


if __name__ == "__main__":
    main()
