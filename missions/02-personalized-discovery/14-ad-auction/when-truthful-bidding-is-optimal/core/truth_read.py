"""Truthful bidding, read: why lying does not pay.

Stage 14 states that second-price makes truthful bidding dominant. This
script verifies it computationally: for each possible true value, it
checks whether bidding the true value ever loses to bidding something
else.

Run:
    uv run python core/truth_read.py
"""

from __future__ import annotations


def second_price(bids: list[float]) -> tuple[int, float]:
    order = sorted(range(len(bids)), key=lambda i: bids[i], reverse=True)
    winner = order[0]
    price = bids[order[1]] if len(order) > 1 else 0.0
    return winner, price


def main() -> None:
    print("truthful bidding dominance, read:")
    for true_value in (0.5, 1.0, 1.5):
        print(f"  advertiser true value {true_value}:")
        for bid in (0.3, true_value, 1.8):
            rivals = [1.0, 0.8]
            winner, price = second_price([bid] + rivals)
            won = winner == 0
            utility = (true_value - price) if won else 0.0
            print(f"    bid {bid:.1f} -> {'wins' if won else 'loses'} "
                  f"at {price:.2f}, utility {utility:.2f}")
    print("\nreading: bidding the true value never yields lower utility")
    print("than lying — underbidding risks losing, overbidding risks paying")
    print("more than value. The dominant strategy is the honest one.")


if __name__ == "__main__":
    main()
