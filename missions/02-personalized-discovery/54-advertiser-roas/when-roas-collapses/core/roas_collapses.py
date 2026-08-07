"""ROAS collapses, read: the extra dollar buys less every time.

Stage 54 detour: the advertiser raises the budget to buy more
conversions. The first extra dollar reaches the audience that was
already inclined; each later dollar reaches a colder one. ROAS falls
as spend scales, and the walk-away line is a spend level.

Run:
    uv run python core/roas_collapses.py
"""

from __future__ import annotations

AOV = 28.0
CONVERSIONS = {1000: 310, 2000: 430, 3000: 455}


def main() -> None:
    print("roas collapses, read (aov $28, cpa target $5):")
    for spend in sorted(CONVERSIONS):
        conversions = CONVERSIONS[spend]
        roas = conversions * AOV / spend
        cpa = spend / conversions
        print(f"  spend ${spend:>4}: conversions {conversions}, "
              f"cpa ${cpa:.2f}, roas {roas:.2f}")
    print("\nreading: doubling the budget buys only 120 more conversions;")
    print("the third thousand buys 25. CPA climbs from $3.23 to $6.59")
    print("and ROAS falls below the $5 target. The marginal dollar is")
    print("the whole story of scaling - the average return hides that")
    print("the next dollar loses money.")


if __name__ == "__main__":
    main()
