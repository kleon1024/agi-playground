"""Feature missing, read: the default value is a silent decision.

Stage 43 detour: a new item arrives with no price yet. The feature
store must serve something, and the default - zero - changes the
item's score and rank as much as the true price would.

Run:
    uv run python core/feature_missing.py
"""

from __future__ import annotations

ITEMS = [
    {"id": "P1001", "price": 49.0, "ctr": 0.032},
    {"id": "P1002", "price": 89.0, "ctr": 0.032},
    {"id": "P1003", "price": 19.0, "ctr": 0.011},
    {"id": "P1004", "price": None, "ctr": 0.025},  # new item, price unknown
]


def score(price: float, ctr: float) -> float:
    return 1000.0 * ctr - 0.5 * price


def main() -> None:
    print("feature missing, read (default price 0 vs true price 39):")
    default_rows = [
        (item["id"], score(0.0 if item["price"] is None else item["price"], item["ctr"]))
        for item in ITEMS
    ]
    true_rows = [
        (item["id"], score(39.0 if item["price"] is None else item["price"], item["ctr"]))
        for item in ITEMS
    ]
    default_order = [r[0] for r in sorted(default_rows, key=lambda r: r[1], reverse=True)]
    true_order = [r[0] for r in sorted(true_rows, key=lambda r: r[1], reverse=True)]
    for item in ITEMS:
        print(f"  {item['id']}: ctr {item['ctr']:.3f}, "
              f"default price ${0.0 if item['price'] is None else item['price']:.0f}")
    print(f"  rank with default price 0:  {default_order}")
    print(f"  rank with true price 39:    {true_order}")
    print("\nreading: the missing price defaulted to zero, which rewards")
    print("the item as if it were free and promotes it to the top.")
    print("The default is a policy choice that looks like bookkeeping;")
    print("the store must make the default explicit and auditable.")


if __name__ == "__main__":
    main()
