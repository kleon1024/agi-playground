"""First price versus second price, read: the payment rule moves revenue.

Stage 28 compares auction payment rules. This script reads the same bid
set under first-price and second-price rules.

Run:
    uv run python core/first_vs_second.py
"""

from __future__ import annotations


def main() -> None:
    bids = [1.20, 1.00, 0.80]
    first_price = max(bids)
    second_price = sorted(bids, reverse=True)[1]
    print("first vs second price, read (bids [1.20, 1.00, 0.80]):")
    print(f"  first price:  winner pays ${first_price:.2f}")
    print(f"  second price: winner pays ${second_price:.2f}")
    print("\nreading: the same auction pays the platform 20 cents more under")
    print("first price — but advertisers know that and shade their bids,")
    print("which is why the honest-bidding property of stage 14 matters.")
    print("Revenue per auction is only half the question; bidder behavior")
    print("under the rule is the other half.")


if __name__ == "__main__":
    main()
