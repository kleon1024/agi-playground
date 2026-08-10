"""The production lane for stage 05: instead of picking a trade rate by hand
and reading off what it does, solve for the trade rate that hits a declared
ad-load target.

`core/value_tree.py` demonstrates the auction mechanics at a few hand-picked
trade rates. A real ads team does not usually set the trade rate directly —
they set a target such as "ads should occupy 15% of served slots" (a policy
and revenue-forecasting decision) and need the trade rate that achieves it
given the current organic score distribution and the current bid landscape.
That is a root-finding problem: ad load is monotonically non-decreasing in
the trade rate (a higher rate never makes the ad harder to insert), so
bisection is guaranteed to converge, and `scipy.optimize.brentq` does exactly
that with a few more guarantees around bracketing than a hand-rolled loop
would bother to check.

This reuses `core/value_tree.py`'s item generator and combination functions
directly — the trade rate found here is only meaningful against the same
scoring function core defines, not a re-derived one.

Requires `scipy`, not part of this repository's base dependency group.

Run:  python scipy_trade_rate.py --target-ad-load 0.15
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "core"))

import value_tree as core  # our from-scratch combination and auction logic
from scipy.optimize import brentq


def ad_load_at_trade_rate(
    slates: list[list[tuple[str, float]]], trade_rate: float, ad_bid: float, ad_p_click: float, top_k: int
) -> float:
    """Across many independent organic rankings ("slates," one per served
    request), what fraction get an ad inserted at this trade rate? A single
    slate only tells you "in or out"; the target is a rate across traffic.
    """
    insertions = sum(
        1
        for slate in slates
        if core.auction_insert(slate, ad_bid=ad_bid, ad_p_click=ad_p_click, trade_rate=trade_rate, top_k=top_k)[
            "inserted"
        ]
    )
    return insertions / len(slates)


def solve_trade_rate(
    slates: list[list[tuple[str, float]]], target_ad_load: float, ad_bid: float, ad_p_click: float, top_k: int
) -> float:
    def gap(trade_rate: float) -> float:
        return ad_load_at_trade_rate(slates, trade_rate, ad_bid, ad_p_click, top_k) - target_ad_load

    # Bracket generously: 0 never inserts (utility 0), and this bid/click rate
    # combination cannot plausibly need a trade rate above 10 to insert on
    # every slate in this synthetic range of organic scores.
    return brentq(gap, 0.0, 10.0, xtol=1e-3)


def run(n_slates: int, target_ad_load: float, ad_bid: float, ad_p_click: float, top_k: int, seed: int) -> None:
    weights = {"click": 0.4, "completion": 0.3, "satisfaction": 0.3}
    slates = []
    for i in range(n_slates):
        items = core.make_items(12, seed=seed * 1000 + i)
        ranked = sorted(
            ((it.item_id, core.combine_additive(it.predictions, weights)) for it in items), key=lambda p: -p[1]
        )
        slates.append(ranked)

    trade_rate = solve_trade_rate(slates, target_ad_load, ad_bid, ad_p_click, top_k)
    achieved = ad_load_at_trade_rate(slates, trade_rate, ad_bid, ad_p_click, top_k)

    print(f"{n_slates} independent slates, target ad load {target_ad_load:.2%}")
    print(f"solved trade rate: {trade_rate:.4f}")
    print(f"achieved ad load at that rate: {achieved:.2%}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-slates", type=int, default=200)
    parser.add_argument("--target-ad-load", type=float, default=0.15)
    parser.add_argument("--ad-bid", type=float, default=3.5)
    parser.add_argument("--ad-p-click", type=float, default=0.22)
    parser.add_argument("--top-k", type=int, default=6)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run(args.n_slates, args.target_ad_load, args.ad_bid, args.ad_p_click, args.top_k, args.seed)


if __name__ == "__main__":
    main()
