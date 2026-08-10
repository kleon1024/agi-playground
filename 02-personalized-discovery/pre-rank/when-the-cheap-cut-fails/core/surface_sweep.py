"""The cheap cut's surface rate, across keep sizes and scorers.

Stage 03's pre-rank exists because the fine-ranker is too expensive to run
on the full catalogue. The question is how much the cheap proxy loses when
it cuts — measured as the surface rate (fraction of the true top-k that
survives) at each keep size, for the cheap proxy, a popularity-only scorer,
and the fine-ranker itself as the ceiling. The long-tail surface rate is
the part the cheap scorers are built to fail on.

Everything is imported from the stage's core.

Run:
    uv run python core/surface_sweep.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))

from pre_rank import (
    evaluate_scorer,
    fine_rank_true,
    make_catalogue,
    pre_rank_cheap_proxy,
    pre_rank_popularity_only,
)


def main() -> None:
    items = make_catalogue(400, seed=42)
    true_scores = {it.item_id: fine_rank_true(it) for it in items}
    k = 20
    true_top_ids = {it.item_id for it in sorted(items, key=lambda it: -true_scores[it.item_id])[:k]}

    print(f"catalogue 400, true top-{k}, keep sizes 50/100/200/300")
    print(f"{'keep':>5} {'scorer':<18} {'surface':>8} {'long-tail':>10} {'rank rho':>9}")
    scorers = (
        ("cheap_proxy", pre_rank_cheap_proxy),
        ("popularity_only", pre_rank_popularity_only),
        ("fine_rank (ceiling)", fine_rank_true),
    )
    for keep in (50, 100, 200, 300):
        for name, scorer in scorers:
            r = evaluate_scorer(name, scorer, items, keep, true_scores, true_top_ids, k)
            print(
                f"{keep:>5} {name:<18} {r['surface_rate_overall']:>8.3f} "
                f"{r['surface_rate_long_tail']:>10.3f} {r['rank_agreement']:>9.3f}"
            )
        print()


if __name__ == "__main__":
    main()
