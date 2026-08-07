"""Ad load, read: every additional ad costs organic value.

Stage 42 treats ad load as a marketplace decision. This script reads
the revenue-versus-organic trade as ad load rises.

Run:
    uv run python core/ad_load.py
"""

from __future__ import annotations


def main() -> None:
    print("ad load, read (10 slots):")
    # First ad is the most valuable, each extra ad earns less and the
    # cheapest ad can destroy more organic value than it brings in.
    ad_rev_per_ad = (0.25, 0.15, 0.05)
    for ads in (0, 1, 2, 3):
        ad_rev = sum(ad_rev_per_ad[:ads])
        organic = (10 - ads) * 0.10
        total = ad_rev + organic
        print(f"  {ads} ad(s): ad revenue ${ad_rev:.2f}, organic value ${organic:.2f}, total ${total:.2f}")
    print("\nreading: each ad adds revenue but displaces an organic slot.")
    print("The total peaks before the maximum ad load — the same trade as")
    print("stage 18's externality, now set by the marketplace decision")
    print("of how many ads a page carries.")


if __name__ == "__main__":
    main()
