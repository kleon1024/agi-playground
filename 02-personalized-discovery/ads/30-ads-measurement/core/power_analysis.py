"""Incrementality, measured: is the lift visible to the experiment?

Stage 30 measures the ad by what it changed. The stage's increment is
0.4 points (0.032 exposed versus 0.028 control). This script asks the
statistical question: at what sample size is that increment actually
visible? It simulates binomial conversion noise over a sample-size
sweep and an effect-size sweep, with a fixed seed.

Run:
    uv run python core/power_analysis.py
"""

from __future__ import annotations

import math
import random


def norm_cdf(x: float) -> float:
    """Standard normal CDF via the error function (stdlib only)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def two_sided_p(z: float) -> float:
    """Two-sided p-value for a normal test statistic."""
    return 2.0 * (1.0 - norm_cdf(abs(z)))


def simulate(
    rng: random.Random, n: int, exposed_cvr: float, control_cvr: float
) -> tuple[float, float, float, float, float, float, float]:
    """Simulate one experiment; return increment, se, ci_half, z, p."""
    exposed = rng.choices([1, 0], weights=[exposed_cvr, 1 - exposed_cvr], k=n)
    control = rng.choices([1, 0], weights=[control_cvr, 1 - control_cvr], k=n)
    p1 = sum(exposed) / n
    p0 = sum(control) / n
    increment = p1 - p0
    se = math.sqrt(p1 * (1 - p1) / n + p0 * (1 - p0) / n)
    z = increment / se if se > 0 else 0.0
    return p1, p0, increment, se, 1.96 * se, z, two_sided_p(z)


def main() -> None:
    exposed_cvr = 0.032
    control_cvr = 0.028
    increment_true = exposed_cvr - control_cvr

    print("incrementality, measured: is the 0.4-point lift visible?")
    print(f"  true rates: exposed {exposed_cvr:.3f}, control {control_cvr:.3f}")
    print(f"  true increment: {increment_true:.3f} (0.4 points)")
    print()

    print("sample-size sweep (0.4-point increment, fixed seed):")
    print("  n per arm | exposed | control | increment | 95% CI         | p")
    rng = random.Random(42)
    for n in (2_000, 8_000, 20_000, 50_000, 200_000, 1_000_000):
        p1, p0, incr, _se, ci_half, _z, p = simulate(
            rng, n, exposed_cvr, control_cvr
        )
        lo, hi = incr - ci_half, incr + ci_half
        visible = "yes" if lo > 0 else "NO"
        print(f"  {n:>9} | {p1:.4f}  | {p0:.4f}  | {incr:+.4f}    "
              f"| {lo:+.4f} to {hi:+.4f} | {p:.3f}  {visible}")
    print()

    print("effect-size sweep at n = 8,000 per arm (fixed seed):")
    print("  increment | 95% CI         | p      | visible")
    rng2 = random.Random(42)
    for incr_true in (0.004, 0.010, 0.020, 0.050):
        p1, p0, incr, _se, ci_half, _z, p = simulate(
            rng2, 8_000, control_cvr + incr_true, control_cvr
        )
        lo, hi = incr - ci_half, incr + ci_half
        visible = "yes" if lo > 0 else "NO"
        print(f"  {incr_true:.3f}    | {lo:+.4f} to {hi:+.4f} | {p:.3f} | {visible}")
    print()

    print("verdict: the 0.4-point increment is buried in binomial noise")
    print("at the sample sizes a small advertiser can reach. The CI")
    print("covers zero at 8,000 users per arm (p > 0.05) and only")
    print("excludes zero at production-scale spend. A big increment is")
    print("visible at the same 8,000-user scale: the experiment is")
    print("sized for the effect, and the ads track's 0.4 points is too")
    print("small for the traffic most campaigns actually buy.")


if __name__ == "__main__":
    main()
