"""Personalization scares, read: a strong prior narrows the slate
before the user has shown anything.

Stage 51 detour: a confident onboarding prior ranks the chosen
category above everything. The first page becomes a wall of one
category, and a user whose real taste is mixed sees a page that
looks like a misread of them.

Run:
    uv run python core/personalization_scares.py
"""

from __future__ import annotations

N_CATEGORIES = 5
ITEMS_PER_CATEGORY = 4
CATEGORY_CTR = [0.042, 0.036, 0.030, 0.024, 0.016]
PRIOR_CATEGORY = 2


def all_items() -> list[tuple[int, int, float]]:
    items: list[tuple[int, int, float]] = []
    for cat in range(N_CATEGORIES):
        for j in range(ITEMS_PER_CATEGORY):
            items.append((cat * ITEMS_PER_CATEGORY + j, cat, CATEGORY_CTR[cat] * (1.0 - 0.02 * j)))
    return items


def top10_categories(items: list[tuple[int, int, float]], prior: set[int], strength: float) -> list[int]:
    ranked = sorted(
        items,
        key=lambda item: item[2] + (strength if item[1] in prior else 0.0),
        reverse=True,
    )
    return [item[1] for item in ranked[:10]]


def main() -> None:
    items = all_items()
    print("personalization scares, read (category mix of the first page):")
    for strength, label in ((0.0, "no prior"), (0.006, "weak prior"), (0.02, "strong prior")):
        cats = top10_categories(items, {PRIOR_CATEGORY}, strength)
        distinct = len(set(cats))
        prior_share = sum(1 for c in cats if c == PRIOR_CATEGORY) / len(cats)
        print(f"  {label:<11} strength {strength:.3f}: {distinct} categories, "
              f"prior category {prior_share:.0%} of page")
    print("\nreading: the onboarding boost concentrates the page on the")
    print("category the user clicked once at signup - from a fifth of")
    print("the page with no prior to two-fifths with a strong one.")
    print("The more the boost owns, the less of the catalogue the user")
    print("sees before proving they want it. A page that narrows on a")
    print("single signup click reads as a misread, and the user never")
    print("comes back to correct it.")


if __name__ == "__main__":
    main()
