"""Wrong shading, read: the two ways to lose under first price.

Stage 39 shades bids under first price. This script reads over-shading
and under-shading against the optimum.

Run:
    uv run python core/wrong_shading.py
"""

from __future__ import annotations


def main() -> None:
    value = 1.00
    cases = [("under-shade", 0.80), ("optimal", 0.50), ("over-shade", 0.20)]
    print("wrong shading, read (value $1.00, optimum bid $0.50):")
    for name, factor in cases:
        bid = value * factor
        win = max(0.0, min(1.0, bid))
        net = (value - bid) * win
        print(f"  {name} (bid ${bid:.2f}): win {win:.2f}, net ${net:.2f}")
    print("\nreading: under-shading wins more but pays too much; over-")
    print("shading keeps more margin but loses auctions. Both lose to")
    print("the optimum — the shading estimate's error is a direct cost,")
    print("which is why first-price bidding is an estimation problem.")


if __name__ == "__main__":
    main()
