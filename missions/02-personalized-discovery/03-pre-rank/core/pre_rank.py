"""Pre-rank: cut a catalogue from thousands of candidates to a hundred, cheaply
enough that the expensive fine-ranker never has to see the rest.

The number that forces this stage to exist is arithmetic, not taste: scoring
every recalled candidate with a model expensive enough to be worth calling
"fine-rank" is affordable at a hundred items and is not affordable at a
thousand. Something cheap has to remove ninety percent of the field first.

That "something cheap" is dangerous in a specific, easy-to-miss way. A
pre-ranker that is merely *correlated* with the fine-ranker on average can
still be *silently wrong* on a slice the average hides — and once an item is
cut here, no downstream model, however good, can recover it. This file makes
that failure reproducible: two pre-rankers, one built from a real (if
partial) signal and one that leans on a signal correlated with quality only
for already-popular items, scored against an oracle this catalogue is small
enough to compute exhaustively.

Two things are measured, and they answer two different questions:

- **Surface rate** — of the items the oracle actually wants in the final
  top-K, what fraction does this pre-ranker's cut even let through? This is
  the number the fine-ranker cannot fix, because it never sees what surface
  rate excludes.
- **Rank agreement (Spearman rho)** — among the items that did survive, does
  the pre-ranker order them the way the oracle would? Good agreement with
  poor surface rate means the pre-ranker is quietly deciding the outcome on
  exactly the items it excludes, while looking fine on paper everywhere else.

Both use k=10, matching this mission's primary_metric (nDCG@10) so the
diagnostic here is measuring the thing the mission is ultimately graded on,
not a proxy for it.

Run:  python pre_rank.py
      python pre_rank.py --catalogue-size 2000 --keep 150 --k 20
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field


@dataclass
class Item:
    item_id: int
    segment: str  # "head" (established, logged interactions) or "long_tail" (cold)
    content_sim: float  # how well the item's content matches this user's taste
    freshness: float  # recency signal, decays for old items
    price_fit: float  # a business feature: fits the user's usual spend band
    popularity: float  # log-scaled interaction count; ~0 for cold items by construction
    noise: float = field(repr=False, default=0.0)  # the part no feature explains


def make_catalogue(
    n: int, seed: int, long_tail_share: float = 0.3, gem_share: float = 0.03
) -> list[Item]:
    """A synthetic catalogue small enough to score exhaustively.

    Ordinary items — head or long-tail — draw content, freshness, and price
    fit from [0, 0.85]. A `gem_share` of long-tail items are "hidden gems"
    reserved above that ceiling, in [0.85, 1.0]: genuinely excellent, and
    exclusively cold, representing the rare new item that is actually great
    rather than merely unproven. Without a reserved tier like this, a large
    enough catalogue always produces a few head items that reach the same
    content_sim by chance, and the point this stage exists to make —
    something truly good can be sitting in the part of the catalogue a
    popularity signal cannot see at all — stops being demonstrable.

    Popularity is generated deliberately, not sampled independently: for a
    head item it is a noisy echo of the same content/freshness/price quality
    that drives the oracle below — the honest version of "popular things tend
    to be good, because of the feedback loop that made them popular." A
    long-tail item has no exposure history yet, so its popularity is pure
    noise near zero, uninformative about its quality regardless of whether it
    is a gem. That gap — informative for head, blind for long-tail — is the
    entire cold-start problem in one line.
    """
    rng = random.Random(seed)
    items = []
    for i in range(n):
        segment = "long_tail" if rng.random() < long_tail_share else "head"
        is_gem = segment == "long_tail" and rng.random() < gem_share
        if is_gem:
            content_sim = rng.uniform(0.85, 1.0)
            freshness = rng.uniform(0.85, 1.0)
            price_fit = rng.uniform(0.85, 1.0)
        else:
            content_sim = rng.uniform(0.0, 0.85)
            freshness = rng.uniform(0.0, 0.85)
            price_fit = rng.uniform(0.0, 0.85)

        if segment == "head":
            quality = 0.5 * content_sim + 0.3 * freshness + 0.2 * price_fit
            popularity = min(1.0, max(0.0, quality + rng.gauss(0, 0.15)))
        else:
            popularity = rng.random() * 0.05  # cold: no exposure, no signal

        items.append(
            Item(
                item_id=i,
                segment=segment,
                content_sim=content_sim,
                freshness=freshness,
                price_fit=price_fit,
                popularity=popularity,
                noise=rng.gauss(0, 0.05),
            )
        )
    return items


def fine_rank_true(item: Item) -> float:
    """The oracle: an expensive model's score, stood in for exactly, because
    the catalogue is small enough to afford it on every item, not just the
    hundred a real serving path would keep. This is the measurement device,
    not a stage of the funnel — a real fine-ranker is trained (stage 04), not
    hand-written.

    Popularity is deliberately absent from this formula. It is a feature a
    cheap scorer might lean on, not a component of what makes an item
    actually worth showing — an item's fit for this user does not depend on
    how many other people have already seen it.
    """
    interaction = item.content_sim * item.freshness
    return (
        0.45 * item.content_sim
        + 0.25 * item.freshness
        + 0.15 * item.price_fit
        + 0.15 * interaction
        + item.noise
    )


def pre_rank_cheap_proxy(item: Item) -> float:
    """A legitimate cheap pre-ranker: mostly content, a little popularity. It
    shares real signal with the oracle on every item, including cold ones,
    because content_sim does not depend on interaction history — a hidden gem
    can still surface here even with near-zero popularity.
    """
    return 0.7 * item.content_sim + 0.3 * item.popularity


def pre_rank_popularity_only(item: Item) -> float:
    """A pre-ranker that looks fine in aggregate and is wrong in a specific
    place: popularity correlates with the oracle for head items (popular
    things tend to also be good matches, by construction of this catalogue),
    so overall correlation can look acceptable. It has no signal at all for
    long-tail items, whose popularity is uniformly near zero — it cannot even
    rank them relative to each other, let alone against head items.
    """
    return item.popularity


def ranks(values: list[float]) -> list[int]:
    """Rank 1 = highest value. Ties broken by index order, which is fine here
    because these are continuous synthetic scores, not measured production
    data with real repeats.
    """
    order = sorted(range(len(values)), key=lambda i: -values[i])
    out = [0] * len(values)
    for position, idx in enumerate(order, start=1):
        out[idx] = position
    return out


def spearman(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    rx, ry = ranks(xs), ranks(ys)
    d2 = sum((a - b) ** 2 for a, b in zip(rx, ry))
    return 1 - (6 * d2) / (n * (n**2 - 1))


def surface_rate(true_top_ids: set[int], kept_ids: set[int]) -> float:
    if not true_top_ids:
        return 0.0
    return len(true_top_ids & kept_ids) / len(true_top_ids)


def evaluate_scorer(name, scorer, items: list[Item], keep: int, true_scores, true_top_ids, k):
    scored = {it.item_id: scorer(it) for it in items}
    kept_items = sorted(items, key=lambda it: -scored[it.item_id])[:keep]
    kept_ids = {it.item_id for it in kept_items}

    overall = surface_rate(true_top_ids, kept_ids)
    long_tail_true_top = {i for i in true_top_ids if _segment_of(items, i) == "long_tail"}
    long_tail_kept = {i for i in kept_ids if _segment_of(items, i) == "long_tail"}
    long_tail_surface = surface_rate(long_tail_true_top, long_tail_kept)

    rho = spearman([scored[it.item_id] for it in kept_items], [true_scores[it.item_id] for it in kept_items])

    return {
        "name": name,
        "surface_rate_overall": overall,
        "surface_rate_long_tail": long_tail_surface,
        "long_tail_true_top_count": len(long_tail_true_top),
        "rank_agreement": rho,
        "kept": len(kept_ids),
    }


def _segment_of(items: list[Item], item_id: int) -> str:
    return next(it.segment for it in items if it.item_id == item_id)


def run_demo(catalogue_size: int, keep: int, k: int, seed: int) -> None:
    items = make_catalogue(catalogue_size, seed)
    true_scores = {it.item_id: fine_rank_true(it) for it in items}
    true_top_ids = {
        it.item_id for it in sorted(items, key=lambda it: -true_scores[it.item_id])[:k]
    }

    print(f"catalogue: {catalogue_size} items, cut to {keep}, measured against the true top-{k}")
    print(f"true top-{k} contains {sum(1 for i in true_top_ids if _segment_of(items, i) == 'long_tail')} long-tail items\n")

    for name, scorer in [
        ("cheap proxy (content + popularity)", pre_rank_cheap_proxy),
        ("popularity-only proxy", pre_rank_popularity_only),
    ]:
        result = evaluate_scorer(name, scorer, items, keep, true_scores, true_top_ids, k)
        print(f"{result['name']}:")
        print(f"  surface rate, overall     {result['surface_rate_overall']:.3f}")
        print(
            f"  surface rate, long-tail   {result['surface_rate_long_tail']:.3f}"
            f"  (of {result['long_tail_true_top_count']} long-tail items in the true top-{k})"
        )
        print(f"  rank agreement (rho)      {result['rank_agreement']:.3f}  among the {result['kept']} kept\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue-size", type=int, default=600)
    parser.add_argument("--keep", type=int, default=60)
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run_demo(args.catalogue_size, args.keep, args.k, args.seed)


if __name__ == "__main__":
    main()
