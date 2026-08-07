"""Advertiser ROAS, read: the platform's revenue rides on the
advertiser's return staying above their exit line.

Stage 54 introduces advertiser economics. The platform earns what
advertisers spend. An advertiser keeps spending only while return on
ad spend (ROAS) clears their target. As a campaign scales, marginal
conversions decay and ROAS falls toward the walk-away line - the
lifecycle that makes advertiser retention a platform concern.

Run:
    uv run python core/roas.py
"""

from __future__ import annotations

WEEKS = [
    {"week": 1, "spend": 1000.0, "conversions": 310},
    {"week": 2, "spend": 1000.0, "conversions": 325},
    {"week": 3, "spend": 1000.0, "conversions": 265},
    {"week": 4, "spend": 1000.0, "conversions": 165},
]

AOV = 28.0
TARGET_ROAS = 5.0


def main() -> None:
    print("advertiser roas, read (spend $1000/week, aov $28):")
    for row in WEEKS:
        revenue = row["conversions"] * AOV
        roas = revenue / row["spend"]
        print(f"  week {row['week']}: spend ${row['spend']:.0f}, "
              f"conversions {row['conversions']}, revenue ${revenue:.0f}, "
              f"roas {roas:.2f}")
    last = WEEKS[-1]["conversions"] * AOV / WEEKS[-1]["spend"]
    print(f"\nreading: roas falls from a strong start to {last:.2f}, "
          f"below the target of {TARGET_ROAS:.1f}.")
    print("The advertiser does not leave at a plateau; they leave when")
    print("the marginal dollar stops paying. The platform that watches")
    print("only its own revenue is watching the advertiser walk away.")


if __name__ == "__main__":
    main()
