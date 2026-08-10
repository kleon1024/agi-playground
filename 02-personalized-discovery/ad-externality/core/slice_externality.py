"""The hidden-slice externality audit: the aggregate hides who pays.

The stage run shows one slate's displacement. The audit asks the
case-finding question at production scale: whose organic value do the ads
actually displace? It draws 20,000 users (fixed seed) in two slices — a
casual slice whose organic items are low-value, and an engaged slice
whose organic items are high-value — shows one ad per user, and reports
per-slice and aggregate displacement and net value. The aggregate says
"keep the ad"; the engaged slice says it destroys value per user.

Run:
    uv run python core/slice_externality.py
"""

from __future__ import annotations

import random


def main() -> None:
    rng = random.Random(20260807)
    casual_n, engaged_n = 15_000, 5_000
    ad_utility = 0.40

    def slice_stats(n: int, lo: float, hi: float) -> tuple[float, float]:
        displaced_sum = 0.0
        for _ in range(n):
            # Three organic items; the ad displaces the bottom-ranked one.
            slate = sorted(rng.uniform(lo, hi) for _ in range(3))
            displaced_sum += slate[0]
        return displaced_sum / n, ad_utility - displaced_sum / n

    casual_displaced, casual_net = slice_stats(casual_n, 0.15, 0.35)
    engaged_displaced, engaged_net = slice_stats(engaged_n, 0.65, 0.95)
    total = casual_n + engaged_n
    agg_displaced = (casual_displaced * casual_n + engaged_displaced * engaged_n) / total
    agg_net = (casual_net * casual_n + engaged_net * engaged_n) / total

    print("hidden-slice externality audit: 20,000 users, one ad per user,")
    print("ad utility 0.40; the ad displaces the bottom-ranked organic item\n")
    print(f"  {'slice':>8} {'share':>7} {'displaced':>10} {'net/user':>9}")
    print(f"  {'casual':>8} {casual_n / total:>7.1%} "
          f"{casual_displaced:>10.4f} {casual_net:>9.4f}")
    print(f"  {'engaged':>8} {engaged_n / total:>7.1%} "
          f"{engaged_displaced:>10.4f} {engaged_net:>9.4f}")
    print(f"  {'aggregate':>8} {'100%':>7} {agg_displaced:>10.4f} "
          f"{agg_net:>9.4f}")

    print("\nreading: the aggregate net is slightly positive, so an ad-load")
    print("decision made on the aggregate keeps the ad. The engaged slice")
    print("loses 0.32 per user -- the ad displaces the high-value organic")
    print("that drives their sessions. Aggregate ad value hides who pays,")
    print("and the slice that pays is the one the platform can least afford")
    print("to damage.")


if __name__ == "__main__":
    main()
