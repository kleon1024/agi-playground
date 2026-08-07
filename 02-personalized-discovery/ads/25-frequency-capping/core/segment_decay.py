"""The hidden-slice audit: aggregate decay looks mild, one segment crashes.

Stage 25 executes one decay curve and reads the cap off it. The audit
asks the case-finding question at production scale: which segment
carries the fatigue? It draws 20,000 impressions (fixed seed) across
three segments with different fatigue curves and different exposure
distributions, and reports aggregate and per-segment CTR plus the share
of impressions served at or below 0.005 CTR.

Run:
    uv run python core/segment_decay.py
"""

from __future__ import annotations

import random

# CTR by exposure count, per segment. Standard is the stage's curve.
CURVES = {
    "casual": [0.050, 0.046, 0.042, 0.038, 0.034, 0.031, 0.028],
    "standard": [0.050, 0.040, 0.030, 0.020, 0.010, 0.005, 0.002],
    "power": [0.060, 0.032, 0.014, 0.006, 0.002, 0.001, 0.0005],
}

# Share of impressions landing on each exposure count (1..7).
EXPOSURE_DIST = {
    "casual": [45, 27, 14, 7, 4, 2, 1],
    "standard": [28, 24, 19, 13, 9, 5, 2],
    "power": [8, 13, 18, 21, 18, 14, 8],
}

N_IMPRESSIONS = {
    "casual": 6_000,
    "standard": 10_000,
    "power": 4_000,
}

DEAD_CTR = 0.005


def draw_segment(rng: random.Random, name: str) -> tuple[list[int], list[float]]:
    """Exposure counts and CTRs for one segment's impressions."""
    exposures: list[int] = []
    ctrs: list[float] = []
    for _ in range(N_IMPRESSIONS[name]):
        exp = rng.choices(range(1, 8), weights=EXPOSURE_DIST[name], k=1)[0]
        exposures.append(exp)
        ctrs.append(CURVES[name][exp - 1])
    return exposures, ctrs


def dead_share(exposures: list[int], name: str) -> float:
    return sum(1 for e in exposures if CURVES[name][e - 1] <= DEAD_CTR) / len(exposures)


def mean(ctrs: list[float]) -> float:
    return sum(ctrs) / len(ctrs)


def main() -> None:
    rng = random.Random(20260808)
    per_segment: dict[str, tuple[list[int], list[float]]] = {}
    for name in N_IMPRESSIONS:
        per_segment[name] = draw_segment(rng, name)

    all_ctrs = [c for _, ctrs in per_segment.values() for c in ctrs]
    agg = mean(all_ctrs)

    print("hidden-slice audit: 20,000 impressions, fixed seed")
    print("three segments, three fatigue curves, three exposure\n"
          "distributions; 'dead' = CTR at or below 0.005\n")
    print(f"  {'segment':>9} {'share':>7} {'mean CTR':>9} {'dead share':>11}")
    for name, n in N_IMPRESSIONS.items():
        exposures, ctrs = per_segment[name]
        print(f"  {name:>9} {n / len(all_ctrs):>7.1%} {mean(ctrs):>9.4f} "
              f"{dead_share(exposures, name):>11.1%}")
    print(f"  {'aggregate':>9} {'100%':>7} {agg:>9.4f} "
          f"{sum(dead_share(e, n) * N_IMPRESSIONS[n] for n, (e, _) in per_segment.items()) / len(all_ctrs):>11.1%}")

    # The fix: cap where the segment's marginal CTR stops earning.
    print("\nfix comparison: one global cap vs per-segment caps")
    print("  global cap 3 (from the aggregate curve):")
    global_cut = 0
    global_lost = 0.0
    for name in N_IMPRESSIONS:
        exposures, ctrs = per_segment[name]
        cut = sum(1 for e in exposures if e > 3)
        lost = sum(c for e, c in zip(exposures, ctrs) if e > 3)
        global_cut += cut
        global_lost += lost
        print(f"    {name:>9}: cut {cut:>5} impressions, "
              f"{lost:>6.1f} expected clicks lost")
    print(f"    {'total':>9}: cut {global_cut:>5} impressions, "
          f"{global_lost:>6.1f} clicks lost")

    per_seg_caps = {"casual": 7, "standard": 3, "power": 2}
    print("  per-segment caps (casual 7, standard 3, power 2):")
    seg_cut = 0
    seg_lost = 0.0
    for name in N_IMPRESSIONS:
        exposures, ctrs = per_segment[name]
        cut = sum(1 for e in exposures if e > per_seg_caps[name])
        lost = sum(c for e, c in zip(exposures, ctrs) if e > per_seg_caps[name])
        seg_cut += cut
        seg_lost += lost
        print(f"    {name:>9}: cut {cut:>5} impressions, "
              f"{lost:>6.1f} expected clicks lost")
    print(f"    {'total':>9}: cut {seg_cut:>5} impressions, "
          f"{seg_lost:>6.1f} clicks lost")

    print("\nreading: aggregate CTR 0.03-ish looks healthy while the power")
    print("slice runs far below it with a large dead share. A cap read off")
    print("the aggregate curve keeps serving the slice that stopped")
    print("clicking, and a global cap trades away healthy casual clicks.")
    print("Stratifying by segment is how the case is found; per-segment")
    print("caps are how the trade is tuned.")


if __name__ == "__main__":
    main()
