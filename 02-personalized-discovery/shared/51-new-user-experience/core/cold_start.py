"""New-user experience, read: the first page is decided before
personalization can see the user.

Stage 51 introduces the new-user problem. A recommender needs
interactions to personalize, and a new user has none. The first page is
therefore served by a default - global popularity - and personalization
only starts to pay once the user has left a trail. Onboarding priors
can shorten the runway, but only if they are right.

Run:
    uv run python core/cold_start.py
    uv run python core/cold_start.py --emit-log /tmp/cold-start-envelope.json

The `--emit-log` flag writes the per-path first-page outcomes so the
production path in `prod/cold_start_audit.py` can answer the
case-finding question of the stage: the aggregate first-page number is
a blend of onboarding paths, and the failing path is invisible until
you stratify by path.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

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


# Production-log cohort rows: how new users are routed, what the first
# page scored, and the seven-day retention each path earns. The wrong
# prior is worse than asking nothing: a confident misread pushes users
# away (the when-personalization-scares detour).
COHORT_PATHS = [
    {"path": "popularity", "traffic": 0.60, "first_page_ndcg": 0.122, "retention": 0.24},
    {"path": "right prior", "traffic": 0.20, "first_page_ndcg": 0.878, "retention": 0.55},
    {"path": "wrong prior", "traffic": 0.10, "first_page_ndcg": 0.000, "retention": 0.18},
    {"path": "no-ask", "traffic": 0.10, "first_page_ndcg": 0.050, "retention": 0.20},
]


def render_cohort() -> None:
    print("\ncohort view (first page by onboarding path):")
    print(f"  {'path':<12} {'traffic':>8} {'first-page ndcg':>15} "
          f"{'retention':>9}")
    for row in COHORT_PATHS:
        print(
            f"  {row['path']:<12} {row['traffic']:>8.0%} "
            f"{row['first_page_ndcg']:>15.3f} {row['retention']:>9.2f}"
        )
    ndcg_agg = sum(r["traffic"] * r["first_page_ndcg"] for r in COHORT_PATHS)
    retention_agg = sum(r["traffic"] * r["retention"] for r in COHORT_PATHS)
    print(f"  {'aggregate':<12} {1.0:>8.0%} {ndcg_agg:>15.3f} "
          f"{retention_agg:>9.2f}")
    print("\n  reading: the aggregate first-page ndcg hides the path")
    print("  structure - the wrong-prior path scores 0.000 and loses")
    print("  more retention than the no-ask baseline, while 60% of new")
    print("  users arrive via popularity. Stratify by onboarding path")
    print("  before declaring the first-page policy healthy.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-log", help="write the cohort rows as JSON")
    args = parser.parse_args()
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
    render_cohort()
    if args.emit_log:
        Path(args.emit_log).write_text(
            json.dumps({"paths": COHORT_PATHS, "popularity_baseline_ndcg": 0.122})
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
