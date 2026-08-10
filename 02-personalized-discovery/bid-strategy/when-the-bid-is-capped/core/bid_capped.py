"""The bid cap, read: capping changes which auctions the advertiser wins.

Stage 27 bids by value. This script reads a bid cap's effect on the win
rate and the average price paid.

Run:
    uv run python core/bid_capped.py
"""

from __future__ import annotations


def main() -> None:
    auctions = [0.04, 0.07, 0.09, 0.12, 0.16]
    value = 0.10
    for cap in (0.10, 0.08, 0.06):
        wins = [p for p in auctions if min(cap, value) >= p]
        price = sum(min(cap, value) for p in auctions if cap >= p)
        print(f"  cap ${cap:.2f}: wins {len(wins)}/5, pays ${price:.2f}")
    print("\nreading: a tighter cap keeps the advertiser out of expensive")
    print("auctions but also out of the cheap ones it could have won at")
    print("higher bids. The cap is a risk dial: lower average price, lower")
    print("reach. Bidding is a budget decision as much as a value one.")


if __name__ == "__main__":
    main()
