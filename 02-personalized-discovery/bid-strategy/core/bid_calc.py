"""Bid strategy, read: the advertiser's value sets the bid.

Stage 27 is the advertiser side of the auction. This script reads how a
target-CPA bid is derived from value and expected CTR.

Run:
    uv run python core/bid_calc.py
"""

from __future__ import annotations


def main() -> None:
    # Advertiser values a conversion at $5 and pays per click.
    conversion_value = 5.0
    cvr = 0.02
    target_cpa = 5.0
    bid = conversion_value * cvr  # per click, in $ units / 100
    print("bid strategy, read (target CPA $5, CVR 2%):")
    print(f"  value per click: ${bid:.2f}")
    print(f"  target CPA bid:  ${target_cpa * cvr:.2f}")
    print("\nreading: the advertiser bids the expected value of a click.")
    print("A target-CPA bid is value x conversion rate — the bid changes")
    print("with the estimate, which is why calibration (stage 16) is the")
    print("advertiser's problem too, not just the platform's.")


if __name__ == "__main__":
    main()
