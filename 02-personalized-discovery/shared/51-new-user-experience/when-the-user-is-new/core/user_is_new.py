"""User is new, read: the onboarding prior is a bet on what the user
will like.

Stage 51 detour: with no trail, the platform can ask the new user
what they are here for. A right prior lifts the first page above
popularity; a wrong one sinks it below - the bet is on the asking
and the honesty of the answer.

Run:
    uv run python core/user_is_new.py
"""

from __future__ import annotations

N_CATEGORIES = 5
ITEMS_PER_CATEGORY = 4
CATEGORY_CTR = [0.042, 0.036, 0.030, 0.024, 0.016]
TRUE_TASTE = {2, 3}


def ndcg(ranked_ids: list[int], relevant: set[int], k: int = 10) -> float:
    gain = 0.0
    ideal = 0.0
    for pos in range(k):
        if pos >= len(ranked_ids):
            break
        rel = 1.0 if ranked_ids[pos] in relevant else 0.0
        discount = 1.0 if pos == 0 else 1.0 / (pos + 1).bit_length()
        gain += rel * discount
        ideal += discount
    return gain / ideal if ideal else 0.0


def all_items() -> list[tuple[int, int, float]]:
    items: list[tuple[int, int, float]] = []
    for cat in range(N_CATEGORIES):
        for j in range(ITEMS_PER_CATEGORY):
            items.append((cat * ITEMS_PER_CATEGORY + j, cat, CATEGORY_CTR[cat] * (1.0 - 0.02 * j)))
    return items


def rank_with_prior(items: list[tuple[int, int, float]], prior: set[int]) -> list[int]:
    return [
        item[0]
        for item in sorted(
            items,
            key=lambda item: (1.0 if item[1] in prior else 0.0, item[2]),
            reverse=True,
        )
    ]


def main() -> None:
    items = all_items()
    relevant = {item_id for item_id, cat, _ in items if cat in TRUE_TASTE}
    popularity = [
        item[0] for item in sorted(items, key=lambda i: i[2], reverse=True)
    ]
    right_prior_set = {2, 3}
    wrong_prior_set = {0, 4}
    right_prior = rank_with_prior(items, right_prior_set)
    wrong_prior = rank_with_prior(items, wrong_prior_set)
    print("user is new, read (first page NDCG@10 with different priors):")
    print(f"  popularity only:            {ndcg(popularity, relevant):.3f}")
    print(f"  onboarding prior on {sorted(right_prior_set)}: {ndcg(right_prior, relevant):.3f}")
    print(f"  onboarding prior on {sorted(wrong_prior_set)}: {ndcg(wrong_prior, relevant):.3f}")
    print("\nreading: the right prior lifts the first page from 0.122 to")
    print("0.878; the wrong one collapses it to 0.000. Onboarding is a")
    print("high-leverage bet - it decides the first page for a user")
    print("with no trail, and it is wrong whenever users do not say")
    print("what they mean or the option set misleads them.")


if __name__ == "__main__":
    main()
