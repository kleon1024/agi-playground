"""The ad externality: every ad displaces an organic result.

The mission's contract states the defining feature: every ad displaces an
organic result. An ad slot that earns revenue also pushes a relevant
organic item out of view. This stage quantifies the displacement — the
organic value lost per ad shown — which is the cost side of the ad
decision the value tree must price.

Run:
    uv run python core/ad_externality.py
"""

from __future__ import annotations


def main() -> None:
    # Top-5 slate: organic values at each slot.
    organic = [0.9, 0.8, 0.7, 0.5, 0.3]
    print("ad displacement, read:")
    print(f"  organic slate values: {organic}")
    for n_ads in range(1, 4):
        kept = organic[: len(organic) - n_ads]
        displaced = sum(organic[len(organic) - n_ads:])
        ad_value = 0.6 * n_ads  # assumed ad utility per slot
        print(f"  {n_ads} ad(s): organic kept {kept} (sum {sum(kept):.1f}), "
              f"displaced {displaced:.1f}, ad value {ad_value:.1f}")
    print("\nreading: the ad's net value is its revenue minus the organic")
    print("value it displaced. Two ads displace 0.8 of organic for 1.2 of")
    print("ad value — the trade is real, and the value tree (stage 05) is")
    print("where the platform decides how much organic it may displace.")


if __name__ == "__main__":
    main()
