"""The production lane for stage 03: replace the hand-written linear proxies
with a gradient-boosted tree model, the standard pre-ranker choice in real
discovery systems because it is cheap at inference, handles feature
interactions without hand-specifying them, and tolerates missing/sparse
features common in a candidate set this early in the funnel.

This script reuses `core/pre_rank.py`'s synthetic catalogue and its oracle
(`fine_rank_true`) rather than duplicating them — the point of comparing a
real tool against the from-scratch version is that both are judged against
the exact same ground truth, not a re-derived one. Only the scorer changes:
a `LGBMRanker` trained on (features -> oracle score) in place of a hand-tuned
linear combination.

The evaluation is identical to core's: surface rate overall and by segment,
plus rank agreement among the kept set. What should differ from the core
demo is the *mechanism* generating the score, not the questions asked of it —
a production pre-ranker earns its keep by clearing the same bar the toy
proxies were held to, not a friendlier one.

Requires `lightgbm`, not part of this repository's base dependency group
(the `core/` path has no such requirement, deliberately). Install it in a
lane that also has a compiler toolchain available, then:

Run:  python lgbm_pre_rank.py --catalogue-size 600 --keep 60 --k 10
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "core"))

import lightgbm as lgb
import pre_rank as core  # our from-scratch catalogue and oracle

FEATURE_NAMES = ["content_sim", "freshness", "price_fit", "popularity"]


def to_features(item: core.Item) -> list[float]:
    return [item.content_sim, item.freshness, item.price_fit, item.popularity]


def train_lgbm_scorer(items: list[core.Item], true_scores: dict[int, float]) -> lgb.Booster:
    """Train a regressor against the oracle score directly. A real system
    trains against logged labels (click, dwell, ...), not an oracle it does
    not have — this stands in for "the pre-ranker learns to approximate what
    the expensive model would have said," which is exactly what a pre-ranker
    is for.
    """
    x = [to_features(it) for it in items]
    y = [true_scores[it.item_id] for it in items]
    dataset = lgb.Dataset(x, label=y, feature_name=FEATURE_NAMES)
    params = {
        "objective": "regression",
        "num_leaves": 15,
        "learning_rate": 0.1,
        "min_data_in_leaf": 5,
        "verbosity": -1,
    }
    return lgb.train(params, dataset, num_boost_round=80)


def run(catalogue_size: int, keep: int, k: int, seed: int) -> None:
    items = core.make_catalogue(catalogue_size, seed)
    true_scores = {it.item_id: core.fine_rank_true(it) for it in items}
    true_top_ids = {
        it.item_id for it in sorted(items, key=lambda it: -true_scores[it.item_id])[:k]
    }

    booster = train_lgbm_scorer(items, true_scores)
    predicted = booster.predict([to_features(it) for it in items])
    scored = {it.item_id: float(p) for it, p in zip(items, predicted)}

    result = core.evaluate_scorer(
        "LightGBM pre-rank", lambda it: scored[it.item_id], items, keep, true_scores, true_top_ids, k
    )
    print(f"catalogue: {catalogue_size} items, cut to {keep}, measured against the true top-{k}\n")
    print(f"{result['name']}:")
    print(f"  surface rate, overall     {result['surface_rate_overall']:.3f}")
    print(
        f"  surface rate, long-tail   {result['surface_rate_long_tail']:.3f}"
        f"  (of {result['long_tail_true_top_count']} long-tail items in the true top-{k})"
    )
    print(f"  rank agreement (rho)      {result['rank_agreement']:.3f}  among the {result['kept']} kept")
    print(
        "\nfeature importance (gain):",
        dict(zip(FEATURE_NAMES, booster.feature_importance(importance_type="gain").tolist())),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue-size", type=int, default=600)
    parser.add_argument("--keep", type=int, default=60)
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run(args.catalogue_size, args.keep, args.k, args.seed)


if __name__ == "__main__":
    main()
