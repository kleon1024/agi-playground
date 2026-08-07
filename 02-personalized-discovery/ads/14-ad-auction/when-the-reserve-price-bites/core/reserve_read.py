"""The reserve price, read: what the one-bidder case forces.

Second-price with a single bidder pays the platform zero. The fix is a
reserve price — a minimum the winner must clear. This script extends the
stage's auction with a reserve and shows how it changes both allocation
and revenue.

Run:
    uv run python core/reserve_read.py
"""

from __future__ import annotations


def second_price_with_reserve(bids: list[float], reserve: float) -> tuple[int, float]:
    eligible = [i for i, b in enumerate(bids) if b >= reserve]
    if not eligible:
        return -1, 0.0
    order = sorted(eligible, key=lambda i: bids[i], reverse=True)
    winner = order[0]
    price = bids[order[1]] if len(order) > 1 else reserve
    return winner, price


def main() -> None:
    print("reserve price, read:")
    for reserve in (0.0, 0.70, 0.85, 0.95):
        winner, price = second_price_with_reserve([1.00, 0.80], reserve)
        outcome = f"winner bidder {winner} at {price:.2f}" if winner >= 0 else "no sale"
        print(f"  reserve {reserve:.2f}: bids [1.00, 0.80] -> {outcome}")
    print("\nreading: at reserve 0 the two-bidder auction pays 0.80; at 0.85")
    print("the second bidder is out and the winner pays the reserve; at 0.95")
    print("the top bid still clears and pays 0.95 — the reserve both floors")
    print("revenue and can kill a sale. Setting it is the platform's call.")


if __name__ == "__main__":
    main()
