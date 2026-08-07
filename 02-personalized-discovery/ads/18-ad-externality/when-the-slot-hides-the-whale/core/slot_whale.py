"""The whale slot, read: one high-value organic item hides the externality.

The stage audit shows the aggregate net value of an ad. This read asks
the follow-up: what does the distribution of displacement look like when
a slate contains one exceptionally valuable organic item — a breaking
story, the product the user was searching for? In 90 percent of
impressions the whale ranks above the ad's slot and displacement is
small; in 10 percent the whale is the marginal item and the ad displaces
it. The average hides the tail, and the tail is where the user's most
valuable result dies.

Run:
    uv run python core/slot_whale.py
"""

from __future__ import annotations

import random


def main() -> None:
    rng = random.Random(20260807)
    n = 10_000
    whale = 0.95
    # 90%: the whale ranks above the ad's slot, which displaces a small
    # bottom item. 10%: the whale is the marginal item the ad displaces.
    displaced: list[float] = []
    for _ in range(n):
        small_draw = rng.uniform(0.10, 0.20)
        if rng.random() < 0.90:
            displaced.append(small_draw)
        else:
            displaced.append(whale)

    avg = sum(displaced) / n
    tail = sorted(displaced)
    p50 = tail[int(0.50 * n) - 1]
    p90 = tail[int(0.90 * n) - 1]
    p99 = tail[int(0.99 * n) - 1]
    top = tail[-1]

    print("whale-slot read: 10,000 impressions; one slate in ten carries a")
    print("0.95 whale at the ad's position\n")
    print(f"  {'metric':>14} {'value':>8}")
    print(f"  {'average':>14} {avg:>8.4f}")
    print(f"  {'P50':>14} {p50:>8.4f}")
    print(f"  {'P90':>14} {p90:>8.4f}")
    print(f"  {'P99':>14} {p99:>8.4f}")
    print(f"  {'max (whale)':>14} {top:>8.4f}")

    print("\nreading: the average displacement hides the whale -- P99 is")
    print("more than four times the average, and the max is the whale")
    print("itself. An externality decision made on the average prices the")
    print("routine slots and ignores the 10 percent of impressions where")
    print("the ad kills the user's single most valuable result. The tail,")
    print("not the mean, is the decision number.")


if __name__ == "__main__":
    main()
