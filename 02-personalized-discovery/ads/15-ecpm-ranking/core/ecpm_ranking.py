"""ECPM ranking: why the highest bid does not always win.

An ad's value to the platform is not the bid — it is the expected revenue:
bid times the probability of a click (pCTR), scaled to a thousand
impressions (eCPM). Ranking by eCPM means a lower bid with a much higher
click rate can beat a higher bid, which is the economic core of ad
ranking. This stage implements it.

Run:
    uv run python core/ecpm_ranking.py
"""

from __future__ import annotations


def ecpm(bid: float, pctr: float) -> float:
    return bid * pctr * 1000


def main() -> None:
    ads = [
        ("Ad A", 2.00, 0.05),
        ("Ad B", 0.50, 0.30),
        ("Ad C", 1.00, 0.12),
    ]
    print("eCPM ranking, read:")
    ranked = sorted(ads, key=lambda a: ecpm(a[1], a[2]), reverse=True)
    for name, bid, pctr in ranked:
        print(f"  {name:<5} bid {bid:.2f}  pCTR {pctr:.2f}  eCPM {ecpm(bid, pctr):.2f}")
    print("\nreading: Ad B has the lowest bid but the highest eCPM — it wins.")
    print("Ranking by bid would show the wrong ad; ranking by expected")
    print("revenue is what the platform actually earns.")


if __name__ == "__main__":
    main()
