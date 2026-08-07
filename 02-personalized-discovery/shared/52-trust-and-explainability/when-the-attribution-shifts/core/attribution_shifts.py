"""Attribution shifts, read: the headline changes with the baseline.

Stage 52 detour: an attribution is a statement about an item against a
counterfactual, not a property of the item alone. The same item, the
same model, and the same score produce a different largest contribution
depending on which baseline the explanation tool subtracts. Against the
zero baseline the headline is 'similar users bought' - unverifiable.
Against the population-mean baseline the headline is 'you viewed this
category' - verifiable. The user sees whichever headline the tool's
baseline picks, so the baseline is a product decision, not a
mathematical detail.

Run:
    uv run python core/attribution_shifts.py
"""

from __future__ import annotations

# The shown item's feature values and model weights, as in the stage.
FEATURES = [
    ("price", 3.0, -0.008),
    ("category affinity", 0.2, 0.040),
    ("similar users bought", 0.9, 0.022),
    ("you viewed this category", 0.4, 0.035),
]
# Population means for the same features: the baseline the explanation
# tool subtracts in the "mean" mode.
MEANS = {
    "price": 2.8,
    "category affinity": 0.5,
    "similar users bought": 0.85,
    "you viewed this category": 0.25,
}


def contributions(baseline: dict[str, float]) -> list[tuple[str, float]]:
    out = []
    for name, value, weight in FEATURES:
        out.append((name, weight * (value - baseline.get(name, 0.0))))
    return out


def headline(contribs: list[tuple[str, float]]) -> str:
    return max(contribs, key=lambda c: c[1])[0]


def render() -> None:
    zero = contributions({})
    mean = contributions(MEANS)
    print("attribution shifts, read (largest contribution per baseline):")
    print(f"  {'feature':<24} {'zero baseline':>14} {'mean baseline':>14}")
    by_name = {name: (c0, c1) for (name, c0) in zero
               for n1, c1 in mean if n1 == name}
    for name, (c0, c1) in by_name.items():
        print(f"  {name:<24} {c0:>+14.4f} {c1:>+14.4f}")
    print(f"\n  zero-baseline headline:  '{headline(zero)}'")
    print(f"  mean-baseline headline:   '{headline(mean)}'")
    print("\nreading: the same item, the same model, the same score -")
    print("the headline flips from 'similar users bought' (unverifiable)")
    print("to 'you viewed this category' (verifiable) when the baseline")
    print("changes from zero to the population mean. Neither number is")
    print("wrong; attribution is defined against the counterfactual.")
    print("The question for the product is which counterfactual matches")
    print("what the user would compare against - the baseline the")
    print("explanation tool picks decides which claim the user sees.")


if __name__ == "__main__":
    render()
