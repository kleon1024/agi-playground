"""The ad auction: second-price, and why the winner pays less.

Ads compete for the same slots as organic results, and the allocation is
an auction, not a ranking. The canonical design is second-price: the
highest bidder wins but pays the second-highest bid, which makes truthful
bidding the dominant strategy — bidders cannot improve their position by
lying about value. This stage implements the mechanism and shows the
consequence.

Run:
    uv run python core/ad_auction.py
"""

from __future__ import annotations


def second_price(bids: list[float]) -> tuple[int, float]:
    """Return (winner_index, price_paid)."""
    order = sorted(range(len(bids)), key=lambda i: bids[i], reverse=True)
    winner = order[0]
    price = bids[order[1]] if len(order) > 1 else 0.0
    return winner, price


def main() -> None:
    scenarios = {
        "two bidders": [1.00, 0.80],
        "three bidders": [1.20, 1.00, 0.60],
        "one bidder": [0.90],
    }
    print("second-price auction, read per scenario:")
    for name, bids in scenarios.items():
        winner, price = second_price(bids)
        print(f"  {name:<14} bids {bids} -> winner bidder {winner} "
              f"at {price:.2f}")
    print("\nreading: the winner pays the second-highest bid, not their own.")
    print("Truthful bidding is dominant: bid your true value, because your")
    print("bid sets your chance of winning but the second bid sets your price.")


if __name__ == "__main__":
    main()
