"""The reserve moves revenue, read: the floor trades fill for price.

Stage 28 optimizes the reserve. This script reads the expected revenue
across reserves on a demand distribution.

Run:
    uv run python core/reserve_revenue.py
"""

from __future__ import annotations


def main() -> None:
    # Expected revenue = price * probability a bid clears the reserve.
    for reserve in (0.0, 0.5, 0.8, 1.0, 1.2):
        p_fill = max(0.0, 1.0 - reserve / 1.5)
        revenue = reserve * p_fill
        print(f"  reserve ${reserve:.1f}: fill {p_fill:.2f}, "
              f"expected revenue ${revenue:.2f}")
    print("\nreading: a zero reserve fills every slot at zero price; a high")
    print("reserve prices each sale high but sells few. The revenue-maximizing")
    print("reserve sits between the two — the optimum is a property of the")
    print("demand curve, which is why it is estimated, not guessed.")


if __name__ == "__main__":
    main()
