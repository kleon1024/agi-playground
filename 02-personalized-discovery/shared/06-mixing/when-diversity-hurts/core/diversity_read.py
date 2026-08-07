"""Diversity that hurts, read: the forced slate underperforms.

Stage 06 assembles slates by beam search with a diversity term. This
script shows what happens when the diversity weight is pushed too high:
the combined value of the slate falls.

Run:
    uv run python core/diversity_read.py
"""

from __future__ import annotations


def main() -> None:
    # Items with (relevance, category). The top two are same-category.
    items = [
        (0.95, "A"), (0.90, "A"), (0.70, "B"), (0.65, "C"),
        (0.40, "D"), (0.30, "E"),
    ]
    print("diversity that hurts, read (slate of 4):")
    # Greedy by relevance: the two strongest items share a category.
    greedy = items[:4]
    greedy_rel = sum(r for r, _ in greedy)
    greedy_cats = len({c for _, c in greedy})
    print(f"  relevance-only: {greedy_rel:.2f} relevance, {greedy_cats} categories")
    # Forced diversity: at least 4 distinct categories in the slate.
    forced = [items[0], items[2], items[3], items[4]]
    forced_rel = sum(r for r, _ in forced)
    forced_cats = len({c for _, c in forced})
    print(f"  forced 4 categories: {forced_rel:.2f} relevance, {forced_cats} categories")
    print(f"  cost of the constraint: {greedy_rel - forced_rel:.2f} relevance")
    print("\nreading: the constraint replaces the second-strongest item")
    print("(0.90) with the best item of a missing category (0.40). The")
    print("trade is real — diversity is bought with relevance, and the")
    print("mixing stage has to decide how much the user actually wants.")


if __name__ == "__main__":
    main()
