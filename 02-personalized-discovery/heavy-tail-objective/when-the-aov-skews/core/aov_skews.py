"""When the AOV skews: the same order rate with a different average
order value changes expected gmv, so the amount model must be
conditional on the order, not folded into one regression.

Run:
    uv run python core/aov_skews.py
"""

from __future__ import annotations


def main() -> None:
    # Two cohorts, same order rate, different AOV.
    rows = [
        ("standard", 0.03, 25.0),
        ("premium", 0.03, 90.0),
        ("flash sale", 0.06, 18.0),
    ]
    print("when the aov skews, read (rate x amount decomposition):")
    print(f"  {'cohort':<12}{'p(order)':>9}{'e(gmv|order)':>14}{'e(gmv)':>9}")
    for name, po, aov in rows:
        print(f"  {name:<12}{po:>9.3f}{aov:>14.2f}{po * aov:>9.2f}")
    print()
    print("reading: expected gmv is the product of an order probability and a")
    print("conditional amount, and the two move independently — a flash sale")
    print("doubles the rate and halves the AOV for the same expected value.")
    print("regressing gmv directly mixes both effects into one coefficient;")
    print("the decomposed read keeps them separate so a product change that")
    print("moves AOV does not silently re-train the order model.")


if __name__ == "__main__":
    main()
