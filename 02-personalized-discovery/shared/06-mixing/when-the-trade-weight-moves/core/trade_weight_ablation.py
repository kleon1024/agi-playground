"""What a mixing weight actually trades off, measured on the fixed catalogue.

Stage 06 teaches the constraint-versus-penalty distinction in prose: a hard
category cap is a promise you can point to, a diversity decay is a number
that trades off against value in a way nobody can defend. This script makes
that trade visible on the stage's own synthetic catalogue — same seed, same
beam search, same value function — by sweeping the two knobs the stage names:
the diversity decay (penalty strength) and the ad trade rate.

The decay sweep reports two numbers per setting: the value the optimizer
maximized (position-weighted, decayed) and the raw value at decay=1.0 (the
underlying utility with no penalty). The gap between the raw value of the
no-penalty slate and the raw value of a decayed slate is the price of
diversity, measured instead of asserted.

The trade-rate sweep reports the ad curve's end point per rate: revenue and
the organic user value displaced. The stage's default rate (3.0) was tuned
only to make displacement observable; this sweep shows where the knee is.

Run:
    uv run python core/trade_weight_ablation.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))

from slate_mixing import (
    beam_search_slate,
    category_counts,
    make_ads,
    make_catalogue,
    rank_by_value,
    slate_value,
    trade_curve,
)


def main() -> None:
    seed = 42
    k = 5
    catalogue = make_catalogue(9, seed)
    ads = make_ads(4, seed)

    print("A. diversity-decay sweep (penalty strength), beam width 2, no cap")
    print(f"{'decay':>6} {'categories':<26} {'value@decay':>11} {'raw value':>10} {'raw vs no-penalty':>18}")
    no_penalty = beam_search_slate(catalogue, k, 2, diversity_decay=1.0, category_cap=None)
    no_penalty_raw = slate_value(no_penalty, diversity_decay=1.0)
    for decay in (0.0, 0.25, 0.5, 0.75, 1.0):
        slate = beam_search_slate(catalogue, k, 2, diversity_decay=decay, category_cap=None)
        counts = category_counts(slate)
        cats = " ".join(f"{c}:{counts[c]}" for c in sorted(counts))
        at_decay = slate_value(slate, diversity_decay=decay)
        raw = slate_value(slate, diversity_decay=1.0)
        print(
            f"{decay:>6.2f} {cats:<26} {at_decay:>11.4f} {raw:>10.4f} "
            f"{raw - no_penalty_raw:>+18.4f}"
        )

    capped = beam_search_slate(catalogue, k, 2, diversity_decay=1.0, category_cap=2)
    print(
        f"\nconstraint reference (cap=2, decay=1.0): "
        f"categories {category_counts(capped)}, raw value {slate_value(capped, diversity_decay=1.0):.4f}"
    )

    print("\nB. ad trade-rate sweep (ad load 4): revenue vs organic value displaced")
    organic = rank_by_value(catalogue)
    print(f"{'trade rate':>10} {'revenue':>9} {'displaced':>10} {'per $ revenue':>14}")
    for rate in (0.5, 1.0, 2.0, 3.0, 5.0, 10.0):
        curve = trade_curve(organic, ads, rate, k)
        revenue, displaced = curve[-1][1], curve[-1][2]
        per_dollar = revenue / displaced if displaced else float("inf")
        print(f"{rate:>10.1f} {revenue:>9.3f} {displaced:>10.4f} {per_dollar:>14.2f}")


if __name__ == "__main__":
    main()
