"""Take rate too high, read: the revenue collapse at the extreme.

Stage 42 studies the take rate. This script reads the far end of the
curve where the platform's cut kills the marketplace.

Run:
    uv run python core/rate_too_high.py
"""

from __future__ import annotations


def main() -> None:
    print("take rate too high, read:")
    for rate in (0.30, 0.50, 0.70, 0.85):
        volume = max(0.0, 1000 * (1.0 - rate * 1.6))
        revenue = rate * volume
        print(f"  rate {rate:.0%}: volume {volume:.0f}, revenue ${revenue:.0f}")
    print("\nreading: revenue peaks around 30-40% and collapses past 70%.")
    print("At 85% the volume is nearly gone and revenue is a fraction of")
    print("the peak — the platform's greed is measured in lost volume,")
    print("which is the same shape as the reserve and ad-load decisions.")


if __name__ == "__main__":
    main()
