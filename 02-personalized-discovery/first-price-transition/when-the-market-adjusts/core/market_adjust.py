"""Market adjustment, read: revenue shifts as bidders learn.

Stage 39 studies the first-price transition. This script reads what
happens to platform revenue as the bidder population converges to
shading.

Run:
    uv run python core/market_adjust.py
"""

from __future__ import annotations


def main() -> None:
    # (phase, average shading factor, platform revenue per auction)
    phases = [
        ("naive (bid full value)", 1.00, 0.95),
        ("transition (learn shading)", 0.70, 0.68),
        ("settled (shade to optimum)", 0.50, 0.42),
    ]
    print("market adjustment, read:")
    for phase, factor, revenue in phases:
        print(f"  {phase}: shading {factor:.2f}, revenue ${revenue:.2f}")
    print("\nreading: as bidders learn to shade, the platform's revenue")
    print("per auction falls — the first-price transition moved revenue")
    print("from the platform to the advertisers over time. A revenue")
    print("forecast that assumes naive bidding overstates the steady state.")


if __name__ == "__main__":
    main()
