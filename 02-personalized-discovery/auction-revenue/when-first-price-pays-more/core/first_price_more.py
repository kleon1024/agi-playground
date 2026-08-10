"""When first price pays more, read: the revenue lift is bidder-dependent.

Stage 28 compares payment rules. This script reads the revenue gap across
two bidder populations.

Run:
    uv run python core/first_price_more.py
"""

from __future__ import annotations


def main() -> None:
    # Naive bidders bid true value; strategic bidders shade to 80%.
    naive = [1.20, 1.00, 0.80]
    shaded = [0.96, 0.80, 0.64]
    for name, bids in (("naive", naive), ("shaded", shaded)):
        first = max(bids)
        second = sorted(bids, reverse=True)[1]
        print(f"  {name} bidders: first ${first:.2f}, second ${second:.2f}, "
              f"gap ${first - second:.2f}")
    print("\nreading: first price pays more when bidders bid truthfully and")
    print("less when they shade. The revenue rule and the bidder population")
    print("are coupled — a revenue comparison is only valid for the bidding")
    print("behavior it assumes.")


if __name__ == "__main__":
    main()
