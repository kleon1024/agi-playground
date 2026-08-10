"""The target CPA binds, read: the bid floor protects the budget.

Stage 27 bids to a target CPA. This script reads what happens when the
auction price rises above the bid the target allows.

Run:
    uv run python core/cpa_binds.py
"""

from __future__ import annotations


def main() -> None:
    value_per_click = 0.10
    print("target CPA binds, read (max bid $0.10/click):")
    for auction_price in (0.06, 0.10, 0.14, 0.20):
        enter = auction_price <= value_per_click
        print(f"  price ${auction_price:.2f}: {'bid' if enter else 'stand down'}")
    print("\nreading: when the auction price passes the click's value, the")
    print("advertiser stops bidding — a win at that price is a loss. The")
    print("target CPA is a walk-away line: the bid protects the budget by")
    print("refusing the auctions that would break it.")


if __name__ == "__main__":
    main()
