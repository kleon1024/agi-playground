"""Trust and explainability, read: an explanation is only as good as
the claim the user can check.

Stage 52 introduces explanation quality. For one shown item, a linear
scorer attributes the decision to its features. The user can verify
some of those claims and not others. The attribution that builds trust
is the one whose largest term the user can actually check.

Run:
    uv run python core/attribution.py
"""

from __future__ import annotations

# The shown item and its feature values, with model weights.
FEATURES = [
    ("price", 3.0, -0.008, "verifiable"),
    ("category affinity", 0.2, 0.040, "verifiable"),
    ("similar users bought", 0.9, 0.022, "unverifiable"),
    ("you viewed this category", 0.4, 0.035, "verifiable"),
]


def main() -> None:
    print("trust and explainability, read (contributions to the score):")
    contributions = [
        (name, value, weight, value * weight, checkable)
        for name, value, weight, checkable in FEATURES
    ]
    total = sum(max(0.0, c[3]) for c in contributions)
    for name, value, weight, contrib, checkable in contributions:
        if contrib >= 0:
            share = contrib / total if total else 0.0
            print(f"  {name:<24} value {value:<4.1f} x weight {weight:+.3f} "
                  f"= {contrib:+.4f} ({share:.0%} of score, {checkable})")
        else:
            print(f"  {name:<24} value {value:<4.1f} x weight {weight:+.3f} "
                  f"= {contrib:+.4f} (penalty, {checkable})")
    top = max(contributions, key=lambda c: c[3])
    print(f"\nreading: the largest contribution is '{top[0]}', which the")
    print("user cannot check - no record of similar users exists on")
    print("their side. The verifiable claims ('you viewed this")
    print("category', 'category affinity') are smaller. Trust is built")
    print("on explanations the user can falsify, not on the term with")
    print("the largest coefficient.")


if __name__ == "__main__":
    main()
