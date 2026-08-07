"""The value tree: collapse a vector of calibrated predictions into the one
scalar a slate actually needs to be ordered by.

Stage 04 hands this stage several numbers per item — p(click), p(completion),
p(satisfaction), predicted dwell — and none of them, alone, is "the" score.
Turning several into one is not a modeling problem; it is a product decision
expressed as arithmetic, and this file makes three parts of that decision
concrete enough to run.

**Weights are the product strategy.** Move the weight on satisfaction versus
click and the slate reorders. That reordering is not a side effect of tuning
a hyperparameter — a platform that weights click at 0.9 and satisfaction at
0.1 optimizes for a different outcome than one that weights them 0.5/0.5, on
the same predictions, for the same users. `sweep_weight` below makes that
reordering something you can watch happen rather than take on faith.

**Additive and multiplicative combination assume different things about the
objectives.** A weighted sum treats objectives as substitutes: a very high
score on one dimension can compensate a very low score on another, so an item
that is highly clickable and mediocre on everything else can still win. A
weighted product treats objectives as requirements: since anything raised to
a positive power is driven toward zero by any factor near zero, an item weak
on even one weighted dimension is punished far harder than an equivalent
weighted sum would punish it — a survey-called-clickbait item does not
merely lose a little ground under a product combination, it collapses.
Neither is "correct"; they encode different beliefs about whether a platform
will accept a bad outcome on one axis in exchange for a great one on another.

**Weights are only meaningful if the inputs are calibrated.** `w=2` on click
is supposed to mean "click matters twice as much as whatever has weight 1."
That claim is false the moment the click number is not a true probability —
multiplying a miscalibrated score by 2 does not double its real-world
meaning, it just doubles whatever the miscalibration happened to produce.
`demo_calibration_precondition` below reruns the same weights against a
deliberately miscalibrated input and shows the ranking move for a reason that
has nothing to do with product strategy.

**Every ad displaces an organic result**, so its insertion is decided by an
explicit trade rate — utility credited per dollar of expected revenue — not
by a separate, unaccountable ad-ranking pass. `auction_insert` folds an ad's
expected revenue into the same scale as the organic value-tree score and asks
one question: does this trade rate make the ad worth more than the weakest
organic item it would remove?

This file does not assemble a slate — permutation, diversity, and beam search
belong to `06-mixing`. Its only job is to turn one item's prediction vector
into one comparable number.

Run:  python value_tree.py
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass

Predictions = dict[str, float]  # calibrated, task -> probability in [0, 1]


@dataclass
class Item:
    item_id: str
    predictions: Predictions


def combine_additive(predictions: Predictions, weights: dict[str, float]) -> float:
    """A weighted sum, normalized so the weights read as shares of one. A
    dimension with weight 0 is fully ignored, and no dimension can veto the
    others — a 0.99 on one axis and a 0.0 on another still average out to
    something in between.
    """
    total_weight = sum(weights.values())
    if total_weight == 0:
        return 0.0
    return sum(weights[t] * predictions[t] for t in weights) / total_weight


def combine_multiplicative(predictions: Predictions, weights: dict[str, float]) -> float:
    """A weighted product: predictions raised to their weight as exponents,
    then multiplied. Weight 0 still means "ignored" (anything^0 = 1), but any
    weighted dimension near 0 drags the whole product toward 0 regardless of
    how high the others are — there is no compensation across dimensions,
    only a requirement that all weighted dimensions be adequate at once.
    """
    score = 1.0
    for task, weight in weights.items():
        p = min(max(predictions[task], 1e-6), 1.0)
        score *= p**weight
    return score


def sweep_weight(
    items: list[Item], task_a: str, task_b: str, mode: str, steps: int = 5
) -> list[tuple[float, list[str]]]:
    """Hold every weight fixed except the one trade between task_a and
    task_b, move it from "all task_a" to "all task_b," and record the
    resulting order at each step. This is the one-causal-variable sweep the
    prose above describes.
    """
    combine = combine_additive if mode == "additive" else combine_multiplicative
    results = []
    for step in range(steps + 1):
        w_b = step / steps
        w_a = 1 - w_b
        weights = {task_a: w_a, task_b: w_b}
        ranked = sorted(items, key=lambda it: -combine(it.predictions, weights))
        results.append((w_b, [it.item_id for it in ranked]))
    return results


def demo_calibration_precondition(items: list[Item], weights: dict[str, float]) -> None:
    """Rerun the same additive weights after inflating one task's predictions
    by a fixed multiplicative miscalibration — the kind a head with a subtly
    wrong loss weighting could plausibly produce — and show the ranking
    change. The point: this reordering was not requested by anyone setting
    product strategy. It is a bug wearing the same interface as a decision.
    """
    honest_ranked = [it.item_id for it in sorted(items, key=lambda it: -combine_additive(it.predictions, weights))]

    miscalibrated_items = [
        Item(it.item_id, {**it.predictions, "click": min(1.0, it.predictions["click"] * 1.6)}) for it in items
    ]
    miscalibrated_ranked = [
        it.item_id for it in sorted(miscalibrated_items, key=lambda it: -combine_additive(it.predictions, weights))
    ]

    print("weights unchanged; click predictions inflated 1.6x (not re-calibrated):")
    print(f"  honest ranking          {honest_ranked}")
    print(f"  miscalibrated ranking   {miscalibrated_ranked}")
    if honest_ranked != miscalibrated_ranked:
        print("  order changed — with no change in product strategy, only in calibration.")
    else:
        print("  order happened to survive this draw; rerun with a different --seed.")


def auction_insert(
    organic_ranked: list[tuple[str, float]], ad_bid: float, ad_p_click: float, trade_rate: float, top_k: int
) -> dict:
    """Fold one ad into an organic ranking by comparing its trade-rate-scaled
    expected revenue against the weakest organic score inside the top_k. If
    it clears that bar, it enters and the item at the bar exits — the
    displaced item's own score is exactly the cost this ad charged the slate.
    """
    ad_utility = trade_rate * ad_bid * ad_p_click
    top = organic_ranked[:top_k]
    if not top or ad_utility <= top[-1][1]:
        return {"inserted": False, "ad_utility": ad_utility, "slate": [i for i, _ in top], "displaced": None}

    merged = sorted(top + [("sponsored_item", ad_utility)], key=lambda pair: -pair[1])[:top_k]
    displaced = next(i for i, _ in top if i not in {m for m, _ in merged})
    return {
        "inserted": True,
        "ad_utility": ad_utility,
        "slate": [i for i, _ in merged],
        "displaced": displaced,
        "displaced_value": next(s for i, s in top if i == displaced),
    }


def make_items(n: int, seed: int) -> list[Item]:
    rng = random.Random(seed)
    items = []
    for i in range(n):
        # A few archetypes, cycled, so the additive/multiplicative contrast
        # is visible rather than averaged away: some items are click-shaped,
        # some are quality-shaped, most are unremarkable in between.
        archetype = i % 4
        if archetype == 0:
            click, completion, satisfaction = rng.uniform(0.7, 0.95), rng.uniform(0.1, 0.3), rng.uniform(0.05, 0.25)
        elif archetype == 1:
            click, completion, satisfaction = rng.uniform(0.15, 0.35), rng.uniform(0.6, 0.9), rng.uniform(0.6, 0.9)
        else:
            click = rng.uniform(0.3, 0.65)
            completion = rng.uniform(0.3, 0.65)
            satisfaction = rng.uniform(0.3, 0.65)
        items.append(
            Item(
                item_id=f"item_{i}",
                predictions={"click": click, "completion": completion, "satisfaction": satisfaction},
            )
        )
    return items


def run_demo(n_items: int, seed: int) -> None:
    items = make_items(n_items, seed)

    print("weight sweep: click <-> satisfaction, additive combination")
    for w_sat, order in sweep_weight(items, "click", "satisfaction", mode="additive", steps=4):
        print(f"  satisfaction weight {w_sat:.2f}: top 3 = {order[:3]}")

    print("\nweight sweep: click <-> satisfaction, multiplicative combination")
    for w_sat, order in sweep_weight(items, "click", "satisfaction", mode="multiplicative", steps=4):
        print(f"  satisfaction weight {w_sat:.2f}: top 3 = {order[:3]}")

    print(
        "\nnotice the multiplicative order moves toward balanced items faster: a"
        " click-shaped item's near-zero satisfaction is punished harder by a"
        " product than by a sum."
    )

    print("\ncalibration precondition:")
    demo_calibration_precondition(items, {"click": 0.5, "completion": 0.25, "satisfaction": 0.25})

    print("\nad auction, explicit trade rate:")
    weights = {"click": 0.4, "completion": 0.3, "satisfaction": 0.3}
    organic_ranked = sorted(
        ((it.item_id, combine_additive(it.predictions, weights)) for it in items), key=lambda pair: -pair[1]
    )
    for trade_rate in (0.2, 0.5, 0.8):
        result = auction_insert(organic_ranked, ad_bid=3.5, ad_p_click=0.22, trade_rate=trade_rate, top_k=6)
        if result["inserted"]:
            print(
                f"  trade_rate={trade_rate:.1f}: ad enters, displaces {result['displaced']}"
                f" (organic value {result['displaced_value']:.3f})"
            )
        else:
            print(f"  trade_rate={trade_rate:.1f}: ad utility {result['ad_utility']:.3f}, does not clear the bar")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-items", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run_demo(args.n_items, args.seed)


if __name__ == "__main__":
    main()
