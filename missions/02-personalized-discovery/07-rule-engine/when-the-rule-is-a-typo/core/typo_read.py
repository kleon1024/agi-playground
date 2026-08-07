"""The rule nobody tested, read: a typo matches nothing, silently.

Stage 07's rule engine applies declarative constraints. This script shows
the failure mode of a rule that references a misspelled attribute: it
matches nothing and nothing complains.

Run:
    uv run python core/typo_read.py
"""

from __future__ import annotations


def evaluate(rules: list[str], item: dict[str, object]) -> bool:
    return all(rule(item) for rule in rules)


def main() -> None:
    items = [
        {"title": "fresh sneakers", "price": 120.0, "in_stock": True},
        {"title": "used jacket", "price": 60.0, "in_stock": True},
        {"title": "vintage lamp", "price": 200.0, "in_stock": False},
    ]
    intended = [
        lambda it: it["price"] <= 150.0,
        lambda it: it["in_stock"] is True,
    ]
    # The typo: "stock" instead of "in_stock" -> KeyError swallowed into False.
    typo = [
        lambda it: it["price"] <= 150.0,
        lambda it: it.get("stock", False) is True,
    ]
    print("the rule nobody tested, read:")
    for item in items:
        want = evaluate(intended, item)
        got = evaluate(typo, item)
        print(f"  {item['title']}: intended {'keep' if want else 'drop'}, "
              f"typo {'keep' if got else 'drop'} "
              f"({'SAME' if want == got else 'SILENT DIFF'})")
    print("\nreading: a typo'd attribute defaults to False, so every item")
    print("is dropped and the empty set looks like a valid rule result.")
    print("Rule engines need a coverage check: every rule must match at")
    print("least one real item, or it is dead code wearing a policy.")


if __name__ == "__main__":
    main()
