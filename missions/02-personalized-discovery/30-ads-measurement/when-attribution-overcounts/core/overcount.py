"""Attribution overcounts, read: last-click owns the whole journey.

Stage 30 measures ad effect. This script reads the overcount when a
single touchpoint is credited with a multi-touch journey.

Run:
    uv run python core/overcount.py
"""

from __future__ import annotations


def main() -> None:
    touchpoints = {"search ad": 0.4, "display ad": 0.2, "email": 0.4}
    print("attribution, read:")
    print(f"  multi-touch shares: {touchpoints}")
    print("  last-click model credits 'email' with 1.0")
    print(f"  overcount: {1.0 - touchpoints['email']:.1f} of the credit")
    print("\nreading: last-click gives the final touchpoint the whole")
    print("conversion, crediting email with 0.6 of value it shared. The")
    print("measurement model decides which channel gets the budget — an")
    print("overcounting model misallocates spend even when the ads work.")


if __name__ == "__main__":
    main()
