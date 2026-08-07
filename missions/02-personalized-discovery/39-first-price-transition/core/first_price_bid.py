"""First-price bidding, read: the transition that forced bid shading.

Stage 39 is the frontier of the ads auction: the industry moved from
second-price to first-price, and advertisers had to learn to shade.
This script reads the optimal shading factor and its revenue effect.

Run:
    uv run python core/first_price_bid.py
"""

from __future__ import annotations


def main() -> None:
    value = 1.00
    # Shading factor: bid = value * factor. Win probability is the bid
    # against a uniform competitor draw on [0, 1].
    for factor in (1.00, 0.80, 0.60, 0.50, 0.40):
        bid = value * factor
        win = max(0.0, min(1.0, bid))
        expected = (value - bid) * win
        print(f"  factor {factor:.2f}: bid ${bid:.2f}, win {win:.2f}, net ${expected:.2f}")
    print("\nreading: the winner pays its own bid, so net is (value - bid)")
    print("times win probability. With a uniform competitor the optimum is")
    print("half the value: bidding $1.00 nets $0.00, bidding $0.50 nets")
    print("$0.25. Shade too little and you overpay; too much and you lose")
    print("auctions you should have won — the detours price both.")


if __name__ == "__main__":
    main()
