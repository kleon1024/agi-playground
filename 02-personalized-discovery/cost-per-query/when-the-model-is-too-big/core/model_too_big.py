"""Model too big, read: the last 0.01 of quality has a price.

Stage 50 detour: doubling the fine-rank model buys a small NDCG gain
at a doubled cost per query. The decision is not whether the bigger
model is better - it is whether the gain clears the budget it spends
across the traffic it serves.

Run:
    uv run python core/model_too_big.py
"""

from __future__ import annotations

# (model, cost per query, ndcg)
MODELS = [
    ("small", 1.0, 0.618),
    ("large", 2.0, 0.631),
]

QUERIES_PER_DAY = 10_000_000


def main() -> None:
    print("model too big, read (fine-rank cost per query, 10M queries/day):")
    for name, cost, ndcg in MODELS:
        daily = cost * QUERIES_PER_DAY
        print(f"  {name:<5} {cost:.1f} units/query, ndcg {ndcg:.3f}, "
              f"daily {daily:,.0f} units")
    print("\nreading: the large model adds 0.013 ndcg and doubles the")
    print("daily cost of the fine-rank stage. Whether that is worth it")
    print("is a budget question: the same units could buy recall depth,")
    print("a cache, or a second experiment. Model size is a cost line,")
    print("and cost per query is the unit it is measured in.")


if __name__ == "__main__":
    main()
