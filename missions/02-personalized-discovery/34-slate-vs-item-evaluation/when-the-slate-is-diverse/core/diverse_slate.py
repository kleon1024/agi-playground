"""Diverse slate, read: the slate metric trades item score for coverage.

Stage 34 evaluates slates, not items. This script reads how the
optimal slate under a diversity-aware metric differs from the item-
score optimum.

Run:
    uv run python core/diverse_slate.py
"""

from __future__ import annotations


def main() -> None:
    # (item, relevance, category)
    items = [
        ("i1", 0.95, "A"),
        ("i2", 0.93, "A"),
        ("i3", 0.91, "A"),
        ("i4", 0.80, "B"),
        ("i5", 0.79, "C"),
    ]

    def item_top3() -> list[str]:
        return [d for d, s, _ in sorted(items, key=lambda x: -x[1])[:3]]

    def diverse_top3() -> list[str]:
        chosen: list[str] = []
        cats: set[str] = set()
        for d, s, c in sorted(items, key=lambda x: -x[1]):
            if c not in cats or len(chosen) < 2:
                chosen.append(d)
                cats.add(c)
            if len(chosen) == 3:
                break
        return chosen

    print("diverse slate, read:")
    print(f"  item-score top-3: {item_top3()}")
    print(f"  diversity-aware:  {diverse_top3()}")
    print("\nreading: the item-score slate is three category-A items; the")
    print("diversity-aware slate drops one for coverage. Both are 'best'")
    print("under different objectives — the evaluation metric has to say")
    print("which one the product wants before the ranker is tuned.")


if __name__ == "__main__":
    main()
