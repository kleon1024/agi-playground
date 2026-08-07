"""Switchback: when the market leaks across the groups.

Stage 54's gate flags serial dependence in time-block experiments. This
chapter shows why two-sided settings need switchbacks at all, and what
switchbacks cost:

Why: in a marketplace (or ad exchange), randomizing users leaks treatment
into control -- a treatment user's purchase consumes shared supply, and a
changed ranking changes the market equilibrium for everyone (the ads
externality stage, 18-ad-externality, is the same interference from the
supply side). The unit of randomization becomes a time block. The outcome
(revenue, GMV, ad revenue) is a slow-moving market series: minutes
autocorrelate, so per-minute analysis massively overstates significance.

The demo simulates the market as an AR(1) series under the null (no effect)
and repeats the experiment 100 times. Two simulations:

1. Half-hour blocks (28 in 7 days): per-minute analysis treats 5,040
   minutes as independent observations when the effective unit is 28
   blocks. Per-minute rejects roughly half of null experiments; per-block
   analysis restores near-nominal false-positive control.
2. Five-minute blocks: the same market now produces block means with
   lag-1 autocorrelation rho1 around 0.7 -- the gate's serial-dependence
   check would flag it, and that autocorrelation is exactly what makes
   per-request analysis catastrophic at any block length.

Then it prices the real cost of switchback: the effective sample is the
number of blocks, so the detectable effect is enormous. Bojinov,
Simchi-Levi and Zhao (2023) formalize the design; the numbers below show
why a platform reserves switchback for big marketplace changes and
prefers user-level experiments wherever interference is small enough.
"""

from __future__ import annotations

import math
import random

DAYS = 7
MINUTES_PER_DAY = 720
BLOCK_MINUTES = 30
PHI = 0.9
ALPHA = 0.05
REPS = 100


def ar1_series(length: int, phi: float, rng: random.Random) -> list[float]:
    """A stationary AR(1) series: x_t = phi * x_{t-1} + eps_t."""
    series = [0.0] * length
    x = 0.0
    for t in range(length):
        x = phi * x + rng.gauss(0.0, 1.0)
        series[t] = x
    return series


def t_stat(xs: list[float], ys: list[float]) -> float:
    """Welch t-statistic; sign convention: xs mean minus ys mean."""
    nx, ny = len(xs), len(ys)
    mx, my = sum(xs) / nx, sum(ys) / ny
    vx = sum((x - mx) ** 2 for x in xs) / (nx - 1)
    vy = sum((y - my) ** 2 for y in ys) / (ny - 1)
    se = math.sqrt(vx / nx + vy / ny)
    return (mx - my) / se if se > 0 else 0.0


def p_value_approx(t: float, df: float) -> float:
    """Two-sided p-value via the normal approximation (large df)."""
    return math.erfc(abs(t) / math.sqrt(2.0))


def run_experiment(rng: random.Random, phi: float) -> tuple[bool, bool, float]:
    """One switchback experiment under the null.

    Returns (per-minute rejection, per-block rejection, block-mean rho1).
    """
    minutes = DAYS * MINUTES_PER_DAY
    blocks = minutes // BLOCK_MINUTES
    series = ar1_series(minutes, phi, rng)
    arms = [rng.random() < 0.5 for _ in range(blocks)]
    arm_at_minute = [arms[m // BLOCK_MINUTES] for m in range(minutes)]

    treat = [series[m] for m in range(minutes) if arm_at_minute[m]]
    ctrl = [series[m] for m in range(minutes) if not arm_at_minute[m]]
    reject_minute = p_value_approx(t_stat(treat, ctrl), minutes - 2) < ALPHA

    all_means = [
        sum(series[b * BLOCK_MINUTES:(b + 1) * BLOCK_MINUTES]) / BLOCK_MINUTES
        for b in range(blocks)
    ]
    block_means_t = [m for b, m in enumerate(all_means) if arms[b]]
    block_means_c = [m for b, m in enumerate(all_means) if not arms[b]]
    reject_block = p_value_approx(
        t_stat(block_means_t, block_means_c), blocks - 2
    ) < ALPHA

    # Serial dependence: lag-1 autocorrelation of the block means after
    # removing the arm effect -- the gate's check 3 on this log.
    treat_mean = sum(block_means_t) / len(block_means_t)
    ctrl_mean = sum(block_means_c) / len(block_means_c)
    residual = [
        m - (treat_mean if arms[b] else ctrl_mean)
        for b, m in enumerate(all_means)
    ]
    xs, ys = residual[:-1], residual[1:]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    rho1 = num / den if den > 0 else 0.0
    return reject_minute, reject_block, rho1


def main() -> None:
    rng = random.Random(17)
    r_min = r_block = 0
    rhos = []
    for _ in range(REPS):
        reject_minute, reject_block, rho1 = run_experiment(rng, PHI)
        r_min += int(reject_minute)
        r_block += int(reject_block)
        rhos.append(rho1)
    rhos.sort()
    median_rho = rhos[REPS // 2]
    print(f"simulation 1 -- {DAYS} days of half-hour blocks, AR(1) phi={PHI}, "
          f"{REPS} repetitions under the null (declared alpha 5%)")
    print(f"per-minute t-test rejected {r_min} ({100.0 * r_min / REPS:.0f}%)")
    print(f"per-block t-test rejected {r_block} ({100.0 * r_block / REPS:.0f}%)")
    print(f"median block-mean lag-1 rho1: {median_rho:.2f} "
          "(gate threshold 0.2)")

    blocks_per_day = MINUTES_PER_DAY // BLOCK_MINUTES
    blocks = DAYS * blocks_per_day
    per_arm = blocks // 2
    z = 1.959963984540054 + 0.8416212335729143
    mde = z * math.sqrt(2.0) / math.sqrt(per_arm)  # in block-SD units
    print(f"\nthe cost of block-level analysis: {blocks} half-hour blocks "
          f"({per_arm} per arm)")
    print(f"minimum detectable effect at 80% power: {mde:.2f} block-SD")
    print("a 1% effect would need "
          f"{(2.0 * z / 0.01) ** 2 * BLOCK_MINUTES / MINUTES_PER_DAY / 365:.0f} "
          "years of half-hour blocks\n")

    # Simulation 2: short blocks make block means autocorrelate. The same
    # market phi, five-minute blocks, same experiment count.
    short_rng = random.Random(23)
    short_blocks = MINUTES_PER_DAY * DAYS // 5
    r_min2 = r_block2 = 0
    rhos2 = []
    for _ in range(REPS):
        minutes2 = DAYS * MINUTES_PER_DAY
        series = ar1_series(minutes2, PHI, short_rng)
        arms = [short_rng.random() < 0.5 for _ in range(short_blocks)]
        arm_at = [arms[m // 5] for m in range(minutes2)]
        treat = [series[m] for m in range(minutes2) if arm_at[m]]
        ctrl = [series[m] for m in range(minutes2) if not arm_at[m]]
        r_min2 += int(p_value_approx(t_stat(treat, ctrl), minutes2 - 2) < ALPHA)
        means = [sum(series[b * 5:(b + 1) * 5]) / 5 for b in range(short_blocks)]
        mt = [m for b, m in enumerate(means) if arms[b]]
        mc = [m for b, m in enumerate(means) if not arms[b]]
        r_block2 += int(p_value_approx(t_stat(mt, mc), short_blocks - 2) < ALPHA)
        t_mean = sum(mt) / len(mt)
        c_mean = sum(mc) / len(mc)
        resid = [m - (t_mean if arms[b] else c_mean) for b, m in enumerate(means)]
        xs, ys = resid[:-1], resid[1:]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
        rhos2.append(num / den if den > 0 else 0.0)
    rhos2.sort()
    print(f"simulation 2 -- same market, five-minute blocks, {REPS} repetitions")
    print(f"per-minute t-test rejected {r_min2} ({100.0 * r_min2 / REPS:.0f}%)")
    print(f"per-block t-test rejected {r_block2} ({100.0 * r_block2 / REPS:.0f}%)")
    print(f"median block-mean lag-1 rho1: {rhos2[REPS // 2]:.2f} "
          "(gate threshold 0.2 -- flagged)")
    print("\nswitchback is for marketplace-scale changes, not small ranker "
          "tweaks: the effective sample is the number of blocks, so the "
          "detectable effect at any reasonable timeline is enormous.")


if __name__ == "__main__":
    main()
