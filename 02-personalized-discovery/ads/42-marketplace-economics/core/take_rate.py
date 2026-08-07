"""Take rate, read: the platform's cut is a demand decision.

Stage 42 is the frontier of the ads business: the platform's take rate
(its share of each transaction) decides volume, and volume decides
revenue. This script reads the revenue curve against the take rate.

Run:
    uv run python core/take_rate.py
"""

from __future__ import annotations


def main() -> None:
    print("take rate, read (revenue = take_rate x volume):")
    for rate in (0.05, 0.15, 0.25, 0.35, 0.45):
        # Volume falls faster than the rate rises.
        volume = 1000 * (1.0 - rate * 1.6)
        revenue = rate * volume
        print(f"  rate {rate:.0%}: volume {volume:.0f}, revenue ${revenue:.0f}")
    print("\nreading: raising the take rate raises revenue per transaction")
    print("but shrinks volume — revenue peaks at 35% here and falls after.")
    print("The platform's cut is a marketplace decision, not a margin")
    print("calculation: too high, and the marketplace dies; the same")
    print("trade governs ad load (the detour) and the reserve (stage 28).")


if __name__ == "__main__":
    main()
