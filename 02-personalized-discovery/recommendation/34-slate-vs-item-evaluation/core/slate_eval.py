"""Slate evaluation, read: the best items are not the best page.

Stage 34 is the frontier of evaluation: item-level metrics rank items,
but the unit shown to a user is a slate. This script reads two slates
where the higher item-score sum loses on a slate-level metric.

Run:
    uv run python core/slate_eval.py
"""

from __future__ import annotations


def main() -> None:
    # (item, relevance, diversity contribution)
    slate_a = [("a1", 0.9, 1), ("a2", 0.85, 1), ("a3", 0.8, 1)]
    slate_b = [("b1", 0.7, 3), ("b2", 0.7, 4), ("b3", 0.7, 5)]

    def item_sum(slate: list[tuple[str, float, int]]) -> float:
        return sum(s for _, s, _ in slate)

    def slate_value(slate: list[tuple[str, float, int]]) -> float:
        # relevance sum with a small diversity multiplier per distinct cover
        distinct = len({d for _, _, d in slate})
        return item_sum(slate) * (1.0 + 0.2 * distinct)

    print("slate evaluation, read:")
    print(f"  slate_a item-score sum: {item_sum(slate_a):.2f}, slate value {slate_value(slate_a):.2f}")
    print(f"  slate_b item-score sum: {item_sum(slate_b):.2f}, slate value {slate_value(slate_b):.2f}")
    print("\nreading: slate_a wins on item scores (2.55 vs 2.10) but loses")
    print("on slate value (3.06 vs 3.36) once diversity counts. Item-level")
    print("metrics rank items; the user experiences the slate, which is")
    print("why stage 06's mixing and this frontier evaluation agree.")


if __name__ == "__main__":
    main()
