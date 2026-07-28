"""Slate assembly: turning a list of scalar item values into an actual page,
where the page's value is not the sum of its items' values.

Stage 05 (the value tree) collapsed each item's prediction vector into one
scalar. Sorting by that scalar and taking the top K is the wrong move the
moment the objective is about the slate as a whole rather than about each
item in isolation: a catalogue with several near-identical high-value items
from one category sorts all of them to the top together, and the result is a
page nobody wants, because the fifth near-duplicate adds almost nothing once
the first one is already shown. The value of a slot depends on what already
occupies the slots before it — that dependency is exactly what turns slate
assembly into a search problem instead of a sort.

This file treats it as one: an exhaustive brute-force optimum over a small
catalogue as the ground truth a practical beam search is measured against,
plus the two things production systems layer on top of that search — a
position discount for lower slots, and paid placement competing inside the
same arithmetic that ranks everything else, priced by what it displaces.

One simplification, disclosed rather than hidden: position weight alone,
with no diversity mechanism, does not need a search at all — sorting by
value and reading off the highest weight to the highest value is already
optimal (a rearrangement fact, not an approximation). Search only earns its
keep once a diversity term or constraint makes an item's marginal value
depend on what has already been picked, which is why every demo below that
is meant to show search *mattering* turns diversity on.

Run:  python slate_mixing.py
"""

from __future__ import annotations

import argparse
import itertools
import math
import random
from dataclasses import dataclass

CATEGORIES = ["sports", "music", "cooking", "news"]


@dataclass(frozen=True)
class Candidate:
    item_id: str
    category: str
    value: float  # stand-in for stage 05's collapsed value-tree score


@dataclass(frozen=True)
class Ad:
    ad_id: str
    bid: float
    p_click: float


def position_weight(position: int) -> float:
    """A DCG-style discount: slot 0 gets weight 1, and every slot after it
    is worth strictly less, on a curve that flattens rather than falling
    off a cliff. The exact shape is a business choice tuned to how users
    actually scan a page; this one is chosen only to make the curve
    legible, and is named here rather than buried in an unexplained
    constant.
    """
    return 1.0 / math.log2(position + 2)


def category_counts(slate: tuple[Candidate, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in slate:
        counts[item.category] = counts.get(item.category, 0) + 1
    return counts


def slate_value(slate: tuple[Candidate, ...], diversity_decay: float = 1.0) -> float:
    """Position-weighted, diversity-discounted total value of an ordered
    slate. `diversity_decay < 1` makes the second item of a category worth
    less than the first, the third worth less still (geometric decay) — a
    penalty *term* in the objective, tunable, and defensible only by
    argument. `diversity_decay == 1.0` disables that penalty entirely; the
    hard category cap enforced during search (see `beam_search_slate` and
    `exhaustive_best_slate`) is the *constraint* version instead, and the
    two are not the same operationally: a constraint is a promise you can
    point to ("never more than two sports items"), a penalty weight is a
    number that trades off against value in a way nobody can point to and
    defend.
    """
    seen: dict[str, int] = {}
    total = 0.0
    for position, item in enumerate(slate):
        prior = seen.get(item.category, 0)
        discount = diversity_decay**prior
        total += item.value * discount * position_weight(position)
        seen[item.category] = prior + 1
    return total


def _cap_ok(slate: tuple[Candidate, ...], candidate: Candidate, category_cap: int | None) -> bool:
    if category_cap is None:
        return True
    return category_counts(slate).get(candidate.category, 0) < category_cap


def beam_search_slate(
    candidates: list[Candidate],
    k: int,
    beam_width: int,
    diversity_decay: float = 1.0,
    category_cap: int | None = None,
) -> tuple[Candidate, ...]:
    """Build the slate one position at a time, keeping only the
    `beam_width` best partial slates seen so far at each step. Beam width 1
    is a greedy fill that still differs from static top-K sorting, because
    it re-scores each candidate's *marginal* value against whatever is
    already in the slate rather than against a fixed, position-free score.
    Widening the beam trades compute for a better chance of not discarding,
    at step 2, the partial slate that step 5 would have preferred — this
    function is never exhaustive at a finite width, which is exactly the
    approximation the rest of this file measures.
    """
    beams: list[tuple[Candidate, ...]] = [()]
    for _ in range(k):
        expansions: list[tuple[Candidate, ...]] = []
        for partial in beams:
            chosen_ids = {c.item_id for c in partial}
            for cand in candidates:
                if cand.item_id in chosen_ids or not _cap_ok(partial, cand, category_cap):
                    continue
                expansions.append(partial + (cand,))
        if not expansions:
            break
        expansions.sort(key=lambda s: -slate_value(s, diversity_decay))
        beams = expansions[:beam_width]
    return max(beams, key=lambda s: slate_value(s, diversity_decay))


def exhaustive_best_slate(
    candidates: list[Candidate],
    k: int,
    diversity_decay: float = 1.0,
    category_cap: int | None = None,
) -> tuple[Candidate, ...]:
    """The ground truth beam search is measured against: every ordered
    arrangement of every k-subset, scored, and the best one kept. This is
    P(n, k) permutations — fine for the catalogue sizes this file uses,
    useless the moment a real catalogue's n or k grows, which is exactly
    why production systems need beam search (or something better) at all.
    """
    best: tuple[Candidate, ...] | None = None
    best_score = float("-inf")
    for perm in itertools.permutations(candidates, k):
        if category_cap is not None:
            counts: dict[str, int] = {}
            over_cap = False
            for item in perm:
                counts[item.category] = counts.get(item.category, 0) + 1
                if counts[item.category] > category_cap:
                    over_cap = True
                    break
            if over_cap:
                continue
        score = slate_value(perm, diversity_decay)
        if score > best_score:
            best_score = score
            best = perm
    if best is None:
        raise ValueError("no feasible slate under this category cap")
    return best


def greedy_top_k(candidates: list[Candidate], k: int) -> tuple[Candidate, ...]:
    """The move this file argues against once the objective is set-level:
    sort once by each item's standalone value and take the top k, never
    re-examining a candidate's marginal contribution against what has
    already been picked.
    """
    return tuple(sorted(candidates, key=lambda c: -c.value)[:k])


def rank_by_value(candidates: list[Candidate]) -> list[Candidate]:
    return sorted(candidates, key=lambda c: -c.value)


def merge_with_ads(
    organic_ranked: list[Candidate], ads: list[Ad], trade_rate: float, k: int
) -> list[tuple[str, float, float, str]]:
    """Merge a fixed organic ranking with a set of ads competing on the same
    axis: an ad's raw score is its expected revenue (bid times predicted
    click probability) converted into utility at the declared trade rate,
    exactly as stage 05's single-ad auction did. Returns the top k
    (item_id, score, revenue, kind) rows in position order; revenue is 0
    for organic rows. One simplification carried over from stage 05,
    named rather than hidden: this merge compares raw scores, not
    position-weighted ones, so a weak ad cannot win cheaply just because it
    would only occupy a low-weight slot — pricing that in is a real
    refinement this file does not make.
    """
    pool: list[tuple[str, float, float, str]] = [(c.item_id, c.value, 0.0, "organic") for c in organic_ranked]
    pool += [(a.ad_id, trade_rate * a.bid * a.p_click, a.bid * a.p_click, "ad") for a in ads]
    pool.sort(key=lambda row: -row[1])
    return pool[:k]


def trade_curve(
    organic_ranked: list[Candidate], ads_by_revenue: list[Ad], trade_rate: float, k: int
) -> list[tuple[int, float, float]]:
    """One point per ad-load level: how many of the available ads (taken in
    descending order of expected revenue — a business spends its best
    inventory first) are allowed to compete for a slot, the revenue that
    buys, and the user value displaced to buy it. `ads_by_revenue` must
    already be sorted descending by bid * p_click.
    """
    organic_only = organic_ranked[:k]
    baseline_value = slate_value(tuple(organic_only))
    points: list[tuple[int, float, float]] = []
    for ad_load in range(len(ads_by_revenue) + 1):
        merged = merge_with_ads(organic_ranked, ads_by_revenue[:ad_load], trade_rate, k)
        revenue = sum(row[2] for row in merged if row[3] == "ad")
        organic_value_remaining = sum(
            position_weight(pos) * next(c.value for c in organic_ranked if c.item_id == row[0])
            for pos, row in enumerate(merged)
            if row[3] == "organic"
        )
        displaced = baseline_value - organic_value_remaining
        points.append((ad_load, revenue, displaced))
    return points


def make_catalogue(n: int, seed: int) -> list[Candidate]:
    rng = random.Random(seed)
    # The first two categories are pinned to "sports" so the catalogue always
    # contains a near-duplicate cluster; the rest cycle through the other
    # categories. This is a deliberately constructed catalogue, not a sampled
    # one — the point is to make the top-K failure mode visible on every run.
    categories = ["sports", "sports"] + [CATEGORIES[i % len(CATEGORIES)] for i in range(max(n - 2, 0))]
    items = []
    for i, category in enumerate(categories[:n]):
        if category == "sports" and i < 2:
            value = rng.uniform(0.82, 0.90)
        else:
            value = rng.uniform(0.35, 0.85)
        items.append(Candidate(item_id=f"item_{i}", category=category, value=value))
    return items


def make_ads(n: int, seed: int) -> list[Ad]:
    rng = random.Random(seed + 777)
    ads = [Ad(ad_id=f"ad_{i}", bid=rng.uniform(1.5, 5.0), p_click=rng.uniform(0.05, 0.30)) for i in range(n)]
    return sorted(ads, key=lambda a: -(a.bid * a.p_click))


def run_demo(
    catalogue_size: int,
    k: int,
    beam_width: int,
    category_cap: int,
    diversity_decay: float,
    ad_load: int,
    trade_rate: float,
    seed: int,
) -> None:
    catalogue = make_catalogue(catalogue_size, seed)
    print(f"catalogue: {catalogue_size} items across {len(CATEGORIES)} categories")
    for c in catalogue:
        print(f"  {c.item_id:>8}  {c.category:>8}  value={c.value:.3f}")

    print("\n1. greedy top-k (sort by value, take top k) -- no diversity mechanism:")
    greedy = greedy_top_k(catalogue, k)
    print(f"  slate: {[c.item_id for c in greedy]}")
    print(f"  categories: {category_counts(greedy)}")

    print(f"\n2. beam search, width={beam_width}, category cap={category_cap} (a constraint):")
    beam_capped = beam_search_slate(catalogue, k, beam_width, diversity_decay=1.0, category_cap=category_cap)
    print(f"  slate: {[c.item_id for c in beam_capped]}")
    print(f"  categories: {category_counts(beam_capped)}")

    print(f"\n3. beam search, width={beam_width}, diversity decay={diversity_decay} (a penalty term):")
    beam_penalized = beam_search_slate(catalogue, k, beam_width, diversity_decay=diversity_decay, category_cap=None)
    print(f"  slate: {[c.item_id for c in beam_penalized]}")
    print(f"  categories: {category_counts(beam_penalized)}")
    print(
        f"  a cap of {category_cap} guarantees at most {category_cap} per category by construction; "
        "a penalty weight only discourages repeats by however much the value gaps allow -- compare "
        "the category counts above, they are not the same promise."
    )

    print(f"\n4. beam width vs. the exhaustive optimum (category cap={category_cap}):")
    pool_perms = math.perm(len(catalogue), k)
    if pool_perms > 200_000:
        print(f"  skipped: {pool_perms} permutations is too many to brute-force in a demo")
    else:
        exhaustive = exhaustive_best_slate(catalogue, k, diversity_decay=1.0, category_cap=category_cap)
        exhaustive_value = slate_value(exhaustive)
        print(f"  exhaustive optimum: {[c.item_id for c in exhaustive]}  value={exhaustive_value:.4f}")
        for width in sorted({1, 2, 3, beam_width, len(catalogue)}):
            approx = beam_search_slate(catalogue, k, width, diversity_decay=1.0, category_cap=category_cap)
            approx_value = slate_value(approx)
            ratio = approx_value / exhaustive_value if exhaustive_value else 1.0
            print(f"  beam width {width:>2}: value={approx_value:.4f}  ({ratio:.1%} of the exhaustive optimum)")

    print("\n5. position weight -- why slot 3 is not worth the same as slot 1:")
    for pos in range(k):
        print(f"  slot {pos}: weight={position_weight(pos):.3f}")

    print("\n6. ad interleaving: revenue bought against user value displaced, by ad load")
    ads = make_ads(ad_load, seed)
    organic_ranked = rank_by_value(catalogue)
    curve = trade_curve(organic_ranked, ads, trade_rate, k)
    for load, revenue, displaced in curve:
        print(f"  ad load {load}: revenue=${revenue:.3f}  user value displaced={displaced:.4f}")
    print(
        "  revenue grows with each additional ad's expected value, taken best-first; user value "
        "displaced tends to grow faster once ads start pushing the *strongest* organic items out "
        "rather than the weakest -- that is the point on the curve worth finding. Where a business "
        "sits on this curve is a business decision; making the curve visible is the engineering "
        "obligation."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue-size", type=int, default=9)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--beam-width", type=int, default=2)
    parser.add_argument("--category-cap", type=int, default=2)
    parser.add_argument("--diversity-decay", type=float, default=0.5)
    parser.add_argument("--ad-load", type=int, default=4)
    # Tuned to 3.0 only so the fixed synthetic ads cross the weakest organic
    # slot and make displacement observable. It is not a business policy.
    parser.add_argument("--trade-rate", type=float, default=3.0)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run_demo(
        args.catalogue_size,
        args.k,
        args.beam_width,
        args.category_cap,
        args.diversity_decay,
        args.ad_load,
        args.trade_rate,
        args.seed,
    )


if __name__ == "__main__":
    main()
