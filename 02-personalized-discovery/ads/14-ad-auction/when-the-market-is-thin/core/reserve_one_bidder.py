"""The thin market, read: one bidder makes the reserve the whole auction.

The stage audit showed a single-bidder auction pays only the reserve.
This read sweeps the reserve in a one-bidder market and shows the
revenue hump: a reserve that is too low leaves money on the table, a
reserve that is too high kills the sale. The hump's peak is the
monopoly reserve (Myerson, 1981).

Run:
    uv run python core/reserve_one_bidder.py
"""

from __future__ import annotations

import random


def main() -> None:
    rng = random.Random(20260807)
    n = 50_000
    print("thin-market read: one bidder per auction, value ~ U(0,1), 50,000 draws")
    print(f"  {'reserve':>8} {'rev/auc':>9} {'sale rate':>10}")
    for reserve in (0.00, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.90):
        revs = 0.0
        sold = 0
        for _ in range(n):
            v = rng.random()
            if v >= reserve:
                revs += reserve
                sold += 1
        print(f"  {reserve:>8.2f} {revs / n:>9.4f} {sold / n:>10.4f}")

    print("\nreading: revenue per auction peaks near reserve 0.50 (0.25), where the")
    print("trade between price and sale probability balances; below it the price")
    print("is too low, above it the sale rate collapses. The stage audit's deep")
    print("market beat this peak: four bidders at reserve 0.50 earned 0.6118 per")
    print("auction. A thin market cannot be fixed by the reserve alone -- depth")
    print("is the primary instrument, the reserve is the fallback.")


if __name__ == "__main__":
    main()
