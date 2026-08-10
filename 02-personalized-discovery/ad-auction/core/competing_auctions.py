"""Competition-stratified auction revenue audit.

Second-price revenue comes from competition, not from the auction rule
alone. This audit sweeps the number of bidders per auction over a fixed
seed and shows where revenue per auction goes: more bidders raise both
the sale rate and the price, and a thin market leans on the reserve.

Run:
    uv run python core/competing_auctions.py
"""

from __future__ import annotations

import random


def second_price_revenue(bids: list[float], reserve: float) -> tuple[float, bool]:
    """Second-price revenue with a reserve; (revenue, sold)."""
    eligible = [b for b in bids if b >= reserve]
    if not eligible:
        return 0.0, False
    eligible.sort(reverse=True)
    price = eligible[1] if len(eligible) > 1 else reserve
    return price, True


def main() -> None:
    rng = random.Random(20260807)
    reserve = 0.5
    n_auctions = 20_000
    print("competition audit: 20,000 auctions per bidder count, values ~ U(0,1)")
    print(f"reserve {reserve:.2f}; revenue per auction and where it comes from\n")
    print(f"  {'bidders':>8} {'rev/auc':>9} {'sale rate':>10} {'reserve-bound':>13} "
          f"{'top-bid avg':>11}")
    for n_bidders in (1, 2, 3, 4, 8):
        revs = 0.0
        sold = 0
        reserve_bound = 0
        top_sum = 0.0
        for _ in range(n_auctions):
            bids = [rng.random() for _ in range(n_bidders)]
            rev, sold_flag = second_price_revenue(bids, reserve)
            revs += rev
            sold += int(sold_flag)
            if sold_flag and rev == reserve:
                reserve_bound += 1
            top_sum += max(bids)
        bound_share = reserve_bound / sold if sold else 0.0
        print(f"  {n_bidders:>8} {revs / n_auctions:>9.4f} "
              f"{sold / n_auctions:>10.4f} {bound_share:>13.4f} "
              f"{top_sum / n_auctions:>11.4f}")

    print("\nreading: with one bidder the reserve does all the work (every sale")
    print("pays the 0.50 floor); each added bidder raises revenue per auction.")
    print("A market that thins from 4 to 1 bidder loses most of its revenue,")
    print("and no auction-rule change recovers it -- the fix is bidder depth,")
    print("and the reserve is the fallback when depth is gone.")


if __name__ == "__main__":
    main()
