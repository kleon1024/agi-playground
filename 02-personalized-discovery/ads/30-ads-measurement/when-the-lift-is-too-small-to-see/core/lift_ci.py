"""Lift too small to see: the CI, computed analytically.

Stage 30's increment is 0.4 points (0.032 exposed versus 0.028
control). The stage audit simulated the sweep; this detour computes the
confidence-interval width at four sample sizes and the sample size a
proper experiment needs for 80 percent power, with fixed seed for the
simulated rows.

Run:
    uv run python core/lift_ci.py
"""

from __future__ import annotations

import math
import random


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def two_sided_p(z: float) -> float:
    return 2.0 * (1.0 - norm_cdf(abs(z)))


def ci_half_width(n: int, p1: float, p0: float) -> float:
    se = math.sqrt(p1 * (1 - p1) / n + p0 * (1 - p0) / n)
    return 1.96 * se


def required_n(p1: float, p0: float, power: float = 0.80) -> int:
    """Per-arm sample size for a two-sided 5 percent test at power."""
    z_alpha = 1.959964
    z_beta = {0.80: 0.841621, 0.90: 1.281552}[power]
    var = p1 * (1 - p1) + p0 * (1 - p0)
    return math.ceil((z_alpha + z_beta) ** 2 * var / (p1 - p0) ** 2)


def main() -> None:
    exposed_cvr = 0.032
    control_cvr = 0.028
    print("lift too small to see: the CI, computed analytically")
    print(f"  true rates: exposed {exposed_cvr:.3f}, control {control_cvr:.3f}")
    print(f"  true increment: {exposed_cvr - control_cvr:.3f} (0.4 points)")
    print()

    print("CI width for the 0.4-point increment (fixed seed):")
    print("  n per arm | CI half-width | CI            | covers zero")
    rng = random.Random(42)
    for n in (1_000, 10_000, 100_000, 1_000_000):
        exposed = rng.choices([1, 0], weights=[exposed_cvr, 1 - exposed_cvr], k=n)
        control = rng.choices([1, 0], weights=[control_cvr, 1 - control_cvr], k=n)
        p1 = sum(exposed) / n
        p0 = sum(control) / n
        incr = p1 - p0
        half = ci_half_width(n, p1, p0)
        lo, hi = incr - half, incr + half
        print(f"  {n:>9} | {half:+.4f}      | {lo:+.4f} to {hi:+.4f} | "
              f"{'yes' if lo <= 0 else 'NO'}")
    print()

    n80 = required_n(exposed_cvr, control_cvr)
    n90 = required_n(exposed_cvr, control_cvr, 0.90)
    print("sample size to detect the 0.4-point increment:")
    print(f"  80% power: {n80:,} users per arm")
    print(f"  90% power: {n90:,} users per arm")
    print()

    print("CI half-width vs effect size at n = 10,000 per arm:")
    print("  increment | half-width | the CI can see it?")
    for incr_true in (0.004, 0.010, 0.020, 0.050):
        half = ci_half_width(10_000, control_cvr + incr_true, control_cvr)
        visible = "yes" if half < incr_true else "NO"
        print(f"  {incr_true:.3f}    | {half:.4f}     | {visible}")
    print()

    print("reading: the stage's own 0.4-point increment needs about")
    print("28,000 users per arm (80% power) to be seen at all, and the")
    print("CI at 10,000 users is wider than the entire effect. A 1-point")
    print("increment is visible at the same scale: the experiment is")
    print("sized for the effect, so small-lift campaigns need either a")
    print("much larger holdout or a cheaper metric.")


if __name__ == "__main__":
    main()
