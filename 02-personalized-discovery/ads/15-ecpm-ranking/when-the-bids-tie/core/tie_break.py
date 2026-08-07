"""The tie-break rule, read: when the estimate cannot separate two ads.

Two ads tie on estimated eCPM (100.00 each). The ranking needs a rule to
break the tie. Rule by bid picks the high bidder; rule by quality score
picks the high-pCTR ad. Under the estimate they look identical; under
true pCTR they realize different revenue. The choice of rule is a policy
call about which estimation error the platform is willing to eat.

Run:
    uv run python core/tie_break.py
"""

from __future__ import annotations


def ecpm(bid: float, pctr: float) -> float:
    return bid * pctr * 1000


def winner_by_bid(ads: list[tuple[str, float]]) -> str:
    # Higher bid wins the tie; name breaks the remaining tie.
    return max(ads, key=lambda a: (a[1], a[0]))[0]


def winner_by_quality(ads: list[tuple[str, float]]) -> str:
    # Higher estimated pCTR wins the tie; name breaks the remaining tie.
    return max(ads, key=lambda a: (a[2], a[0]))[0]


def main() -> None:
    # (name, bid, estimated pCTR, true pCTR). Estimated eCPM ties at 100.
    scenarios = {
        "conservative estimate": [
            ("Ad A", 2.00, 0.05, 0.05),
            ("Ad X", 1.00, 0.10, 0.12),
        ],
        "generous estimate": [
            ("Ad A", 2.00, 0.05, 0.05),
            ("Ad X", 1.00, 0.10, 0.08),
        ],
    }

    print("tie-break read: two ads tie on estimated eCPM (100.00); the rule")
    print("decides who wins, and true pCTR decides what that slot earns\n")
    for label, ads in scenarios.items():
        print(f"{label}:")
        for name, bid, est, true in ads:
            print(f"  {name}: bid {bid:.2f}, est pCTR {est:.2f} "
                  f"(eCPM {ecpm(bid, est):.2f}), true pCTR {true:.2f}")
        w_bid = winner_by_bid(ads)
        w_qual = winner_by_quality(ads)
        true_rev = {name: ecpm(bid, true) for name, bid, est, true in ads}
        print(f"  tie-break by bid:          {w_bid} wins, "
              f"realized {true_rev[w_bid]:.2f}")
        print(f"  tie-break by quality score:{w_qual} wins, "
              f"realized {true_rev[w_qual]:.2f}\n")

    print("reading: by-bid and by-quality pick the same winner under the")
    print("estimate, different winners under truth. By-bid keeps the")
    print("advertiser's bid a price-taking statement; by-quality invites")
    print("gaming the pCTR estimate, which is model-owned. The measured")
    print("trade: with a conservative estimate, quality wins +20; with a")
    print("generous one, quality loses -20. The rule is chosen for its")
    print("incentives, not for any single scenario's realized revenue.")


if __name__ == "__main__":
    main()
