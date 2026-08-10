"""Metric blind spot, read: the item metric that cannot see the slate.

Stage 34 evaluates slates. This script reads two slates where an
item-level metric scores them equal while a slate metric separates them.

Run:
    uv run python core/metric_blind.py
"""

from __future__ import annotations


def main() -> None:
    slate_a = [("a1", 0.8, 1), ("a2", 0.8, 1), ("a3", 0.8, 1)]
    slate_b = [("b1", 0.8, 3), ("b2", 0.8, 4), ("b3", 0.8, 5)]

    def item_sum(slate: list[tuple[str, float, int]]) -> float:
        return sum(s for _, s, _ in slate)

    def slate_value(slate: list[tuple[str, float, int]]) -> float:
        distinct = len({d for _, _, d in slate})
        return item_sum(slate) * (1.0 + 0.2 * distinct)

    print("metric blind spot, read:")
    print(f"  slate_a item sum {item_sum(slate_a):.2f}, slate value {slate_value(slate_a):.2f}")
    print(f"  slate_b item sum {item_sum(slate_b):.2f}, slate value {slate_value(slate_b):.2f}")
    print("\nreading: the item-level metric ties the slates (2.40 = 2.40)")
    print("while the slate metric separates them (2.88 vs 3.84). A report")
    print("that only averages item scores cannot see the page the user")
    print("actually got.")


if __name__ == "__main__":
    main()
