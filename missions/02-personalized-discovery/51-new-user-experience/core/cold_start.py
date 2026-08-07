"""New-user experience, read: the first page is decided before
personalization can see the user.

Stage 51 introduces the new-user problem. A recommender needs
interactions to personalize, and a new user has none. The first page is
therefore served by a default - global popularity - and personalization
only starts to pay once the user has left a trail. Onboarding priors
can shorten the runway, but only if they are right.

Run:
    uv run python core/cold_start.py
"""

from __future__ import annotations

N_CATEGORIES = 5
ITEMS_PER_CATEGORY = 4
CATEGORY_CTR = [0.042, 0.036, 0.030, 0.024, 0.016]
LIKED = {2, 3}  # the user's true taste: the middle of the catalogue


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
    """(item_id, category, popularity_ctr)"""
    items: list[tuple[int, int, float]] = []
    for cat in range(N_CATEGORIES):
        for j in range(ITEMS_PER_CATEGORY):
            items.append((cat * ITEMS_PER_CATEGORY + j, cat, CATEGORY_CTR[cat] * (1.0 - 0.02 * j)))
    return items


def popularity_rank(items: list[tuple[int, int, float]]) -> list[int]:
    return [item[0] for item in sorted(items, key=lambda i: i[2], reverse=True)]


def main() -> None:
    items = all_items()
    relevant = {item_id for item_id, cat, _ in items if cat in LIKED}
    pop_rank = popularity_rank(items)

    # The user's trail: k interactions, each an impression from the
    # popularity default, a click when the category is liked, with noise.
    rng = __import__("random").Random(11)
    checkpoints = {1, 5, 20}
    print("new-user experience, read (NDCG@10 vs the user's true taste):")
    print(f"  popularity only:               {ndcg(pop_rank, relevant):.3f}")
    clicks = {cat: 0 for cat in range(N_CATEGORIES)}
    impressions = {cat: 0 for cat in range(N_CATEGORIES)}
    for k in range(1, 21):
        # Default exposure follows popularity: category 0 most often.
        cat = rng.choices(range(N_CATEGORIES), weights=CATEGORY_CTR)[0]
        impressions[cat] += 1
        if rng.random() < (0.75 if cat in LIKED else 0.15):
            clicks[cat] += 1
        if k in checkpoints:
            # Laplace-smoothed affinity estimate: (clicks + 0.5) / (impressions + 1).
            estimate = {
                cat: (clicks[cat] + 0.5) / (impressions[cat] + 1.0)
                for cat in range(N_CATEGORIES)
            }
            rank = sorted(
                items,
                key=lambda item: (
                    estimate[item[1]],
                    item[2],
                ),
                reverse=True,
            )
            ranked_ids = [item[0] for item in rank]
            print(f"  personalized after {k:>2} interactions: {ndcg(ranked_ids, relevant):.3f}")
    print("\nreading: at zero interactions personalization has no signal,")
    print("so popularity is the serving policy and the first page is a")
    print("default decision. The trail improves NDCG 0.12 to 0.88 over")
    print("twenty interactions - a short runway, but one that must be")
    print("bridged. Onboarding priors are the lever that moves the")
    print("first page before the trail exists, and the detours show")
    print("what a wrong prior costs.")


if __name__ == "__main__":
    main()
