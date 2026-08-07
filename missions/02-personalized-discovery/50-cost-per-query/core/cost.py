"""Cost per query, read: the cascade is arithmetic with a price tag.

Stage 50 introduces cost per query. Each funnel stage scores a smaller
set with a more expensive model. The cost of a query is the sum over
stages of candidates times per-candidate cost, and the cascade exists
because scoring ten million items with the fine model is unaffordable.

Run:
    uv run python core/cost.py
"""

from __future__ import annotations

# (stage, candidates scored, per-candidate cost units)
STAGES = [
    ("recall (ann)", 100_000, 0.00001),
    ("pre-rank", 1_000, 0.001),
    ("fine-rank", 50, 0.02),
    ("mixing", 20, 0.05),
]

EXHAUSTIVE = 10_000_000 * 0.02


def main() -> None:
    print("cost per query, read (cost units):")
    total = 0.0
    for name, candidates, unit_cost in STAGES:
        cost = candidates * unit_cost
        total += cost
        print(f"  {name:<10} {candidates:>9,} candidates x {unit_cost:.5f} "
              f"= {cost:.1f}")
    print(f"  total per query: {total:.1f} units")
    print(f"  exhaustive fine-rank of 10M items: {EXHAUSTIVE:.0f} units")
    print(f"  per 1M queries, cascade: {total * 1_000_000:,.0f} units")
    print(f"  per 1M queries, exhaustive: {EXHAUSTIVE * 1_000_000:,.0f} units")
    print("\nreading: the cascade costs a fraction of exhaustive scoring,")
    print("and every stage exists to buy the next one a smaller problem.")
    print("Cost per query is the budget that capacity planning spends.")


if __name__ == "__main__":
    main()
