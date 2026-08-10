"""Budget an online experiment before it starts: users, days, levers.

Stage 54's gate decides whether a finished experiment is readable. This
chapter answers the question that has to be answered before the experiment
starts: how many users does it need, how long will it take, and which design
lever actually moves the calendar date.

The split-lies detour asserted a figure — a 2% effect at 80% power needs
39,244 users per arm — and this chapter derives it from the sample-size
formula, then sweeps the four levers that change it:

1. Minimum detectable effect (MDE): halving the effect quadruples the
   sample, because the formula is quadratic in the effect. The MDE is a
   business decision, not a calendar one.
2. Metric variance: sample size scales with the outcome's variance. For a
   proportion metric that variance is p(1-p), so the same absolute lift
   needs about 25x fewer users at a 1% baseline than at a 50% baseline.
3. Variance reduction (CUPED): a pre-experiment covariate with correlation
   rho cuts the sample by the factor (1 - rho^2), because it shrinks the
   outcome variance the sample size formula is written in (Deng, Xu,
   Kohavi and Walker, 2013, WSDM).
4. Traffic allocation and rollout: an unequal split inflates the total
   users needed for the same power, and a controlled ramp adds calendar
   time even when the user count is fixed (Xia, Bhardwaj, Dmitriev and
   Fabijan, 2019, ICSE-SEIP).

Every number is computed from the standard normal approximation — the same
formula the split-lies detour used — with stdlib only and no randomness, so
the output is reproducible byte for byte.

Usage:
    uv run python core/budget_planner.py
"""

from __future__ import annotations

import math

ALPHA = 0.05
# z for a two-sided 5% test and for 80% / 90% power; the same constants the
# split-lies detour hardcodes.
Z_ALPHA = 1.959963984540054
Z_BETA_80 = 0.8416212335729143
Z_BETA_90 = 1.2815515655446004
# The fixed scenario: 10,000 eligible users per day at full traffic, and the
# split-lies experiment that needs 39,244 users per arm.
DAILY_USERS = 10_000.0
EFFECT = 0.02


def norm_cdf(x: float) -> float:
    """Standard normal CDF via the error function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def users_per_arm(delta: float, z_beta: float = Z_BETA_80) -> float:
    """Per-arm sample size: n = 2 (z_alpha/2 + z_beta)^2 / delta^2."""
    return 2.0 * (Z_ALPHA + z_beta) ** 2 / delta**2


def power_at_n(delta: float, n: float) -> float:
    """Power for a per-arm sample of n at standardized effect delta."""
    return norm_cdf(delta * math.sqrt(n / 2.0) - Z_ALPHA)


def per_arm_for_proportion(p: float, abs_lift: float) -> float:
    """Per-arm sample for an absolute lift on a proportion with baseline p."""
    sigma = math.sqrt(p * (1.0 - p))
    return users_per_arm(abs_lift / sigma)


def total_inflation(control_share: float) -> float:
    """Total-user inflation from a split skewed away from 50/50."""
    return (1.0 / control_share + 1.0 / (1.0 - control_share)) / 4.0


def linear_ramp_days(t0: float, ramp_days: float) -> float:
    """Days to reach the needed users under a linear 0-to-100% ramp."""
    return math.sqrt(2.0 * t0 * ramp_days)


def step_ramp_days(t0: float, low_fraction: float, low_days: float) -> float:
    """Days to reach the needed users after a low-fraction hold, then 100%."""
    return t0 + low_days * (1.0 - low_fraction)


def fmt_days(days: float) -> str:
    return f"{days:.1f}".rstrip("0").rstrip(".")


def main() -> None:
    n_base = users_per_arm(EFFECT)
    total_base = 2.0 * n_base
    t0 = total_base / DAILY_USERS

    print("== 1. the number stage 54 asserts, derived ==")
    print(f"two-sided alpha=0.05 (z={Z_ALPHA:.4f}), power 80% "
          f"(z={Z_BETA_80:.4f}), standardized effect delta=0.02")
    print(f"n per arm = 2 * (z_alpha/2 + z_beta)^2 / delta^2 = "
          f"{n_base:,.0f}")
    print(f"total = 2n = {total_base:,.0f} users")
    print("the split-lies detour called this a 2% lift; the formula's unit")
    print("is the outcome's standard deviation, so delta=0.02 means the")
    print("effect is 2% of one sigma, not 2% of the mean: at a 4% CTR,")
    print(f"sigma={math.sqrt(0.04 * 0.96):.3f}, so delta=0.02 is a")
    print(f"{EFFECT * math.sqrt(0.04 * 0.96) * 100:.2f} percentage-point lift;")
    print(f"at a 10% baseline it is "
          f"{EFFECT * math.sqrt(0.1 * 0.9) * 100:.2f} points.\n")

    print("== 2. lever 1 -- the minimum detectable effect ==")
    print(f"{'delta (SD units)':>16} {'users/arm':>12} {'total':>12} "
          f"{'days@10k/day':>13}")
    for d in (0.01, 0.02, 0.05, 0.10):
        n = users_per_arm(d)
        print(f"{d:>16.2f} {n:>12,.0f} {2*n:>12,.0f} "
              f"{fmt_days(2*n/DAILY_USERS):>13}")
    n90 = users_per_arm(EFFECT, Z_BETA_90)
    print(f"power 90% at delta=0.02: {n90:,.0f} users/arm "
          f"({100.0 * n90 / n_base - 100.0:.0f}% more than 80% power).\n")

    print("== 3. the power curve at delta=0.02 ==")
    print(f"{'users/arm':>10} {'power':>8}")
    for n in (10_000, 20_000, round(n_base), 60_000, 80_000):
        print(f"{n:>10,} {100.0 * power_at_n(EFFECT, n):>7.1f}%")
    print("under half the needed sample the test has 52% power: it will")
    print("miss a real 2% effect roughly half the time.\n")

    print("== 4. lever 2 -- metric variance (proportion baselines) ==")
    print("same absolute lift of 0.5 points, power 80%:")
    print(f"{'baseline p':>11} {'sigma':>7} {'users/arm':>12} "
          f"{'relative':>9}")
    n_p01 = per_arm_for_proportion(0.01, 0.005)
    n_p10 = per_arm_for_proportion(0.10, 0.005)
    n_p50 = per_arm_for_proportion(0.50, 0.005)
    print(f"{0.01:>11.2f} {math.sqrt(0.01*0.99):>7.4f} {n_p01:>12,.0f} "
          f"{'1.0x':>9}")
    print(f"{0.10:>11.2f} {math.sqrt(0.10*0.90):>7.4f} {n_p10:>12,.0f} "
          f"{n_p10/n_p01:>8.1f}x")
    print(f"{0.50:>11.2f} {math.sqrt(0.50*0.50):>7.4f} {n_p50:>12,.0f} "
          f"{n_p50/n_p01:>8.1f}x")
    print("sample size scales with p(1-p): the noisy 50% metric needs 25x")
    print("the users of the 1% metric for the same absolute lift.\n")

    print("== 5. lever 3 -- CUPED variance reduction (1 - rho^2) ==")
    print("pre-experiment covariate with correlation rho (Deng et al. 2013):")
    print(f"{'rho':>5} {'factor':>8} {'users/arm':>12} {'days@10k/day':>13}")
    for rho in (0.0, 0.3, 0.5, 0.7, 0.9):
        n = n_base * (1.0 - rho**2)
        print(f"{rho:>5.1f} {1.0 - rho**2:>8.3f} {n:>12,.0f} "
              f"{fmt_days(2*n/DAILY_USERS):>13}")

    print("== 6. lever 4a -- traffic allocation ==")
    print("same power, total users inflated by the split skew:")
    print(f"{'control share':>14} {'variance ratio':>15} {'total users':>13}")
    for w in (0.5, 0.7, 0.8, 0.9):
        print(f"{w:>14.1f} {total_inflation(w):>15.3f} "
              f"{total_base * total_inflation(w):>13,.0f}")
    print("variance of the difference is sigma^2(1/n1 + 1/n2); at a fixed")
    print("total, 50/50 minimizes it, and 80/20 costs 56% more users.\n")

    print("== 7. lever 4b -- the calendar: throughput and ramp ==")
    print(f"the baseline experiment needs {total_base:,.0f} users;")
    print("full-traffic eligible throughput decides the no-ramp date:")
    print(f"{'users/day':>10} {'days':>8}")
    for c in (10_000, 2_000, 500, 100):
        print(f"{c:>10,} {fmt_days(total_base/c):>8}")
    print("\ncontrolled rollout (Xia et al. 2019) adds time even at fixed")
    print(f"users: linear ramp 0-to-100% over R days, t0={fmt_days(t0)} days")
    print("at full traffic:")
    print(f"{'ramp days':>10} {'days to N':>10}")
    for r in (7, 14, 21, 28):
        print(f"{r:>10} {fmt_days(linear_ramp_days(t0, r)):>10}")
    print("step ramp (10% for D days, then 100%):")
    for d in (5, 14):
        print(f"D={d}: {fmt_days(step_ramp_days(t0, 0.1, d))} days")

    print("\n== 8. the verdict: which lever moves the date ==")
    print(f"{'design':>14} {'users/arm':>11} {'total':>11} {'days':>6}")
    rows = [
        ("baseline", n_base, total_base),
        ("MDE 5%", users_per_arm(0.05), 2 * users_per_arm(0.05)),
        ("MDE 1%", users_per_arm(0.01), 2 * users_per_arm(0.01)),
        ("power 90%", n90, 2 * n90),
        ("CUPED r=0.5", n_base * 0.75, total_base * 0.75),
        ("CUPED r=0.9", n_base * 0.19, total_base * 0.19),
    ]
    for name, n, tot in rows:
        print(f"{name:>14} {n:>11,.0f} {tot:>11,.0f} "
              f"{fmt_days(tot/DAILY_USERS):>6}")
    print(f"{'80/20 split':>14} {'--':>11} "
          f"{total_base*1.5625:>11,.0f} "
          f"{fmt_days(total_base*1.5625/DAILY_USERS):>6}")
    print(f"{'ramp 14d':>14} {'--':>11} {'--':>11} "
          f"{fmt_days(linear_ramp_days(t0, 14)):>6}")
    print("\nthe rule: users = power, and power comes from users or from")
    print("variance reduction -- never from reading the result early. When")
    print("the honest MDE at fixed power exceeds throughput times window,")
    print("the design answer is CUPED, a wider MDE agreed with the business,")
    print("or a cheaper design -- not an early peek (Kohavi, Tang and Xu,")
    print("2020; Zhou, Lu and Shallah, 2023).")


if __name__ == "__main__":
    main()
