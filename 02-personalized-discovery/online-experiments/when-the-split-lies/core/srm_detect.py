"""Find the lying split before it poisons the outcome.

Stage 54's gate runs the allocation-ratio check as one validity condition.
This chapter drills into the single most common way the split lies: the
bucketing hash drifts from the declared ratio. The demo below is a
one-constant edit — the bucket threshold was changed from 50 to 52 while the
experiment config still says 50/50 — and it shows three things:

1. How the bug shows up: the observed split deviates from the declared
   split, and the deviation grows with traffic until the chi-square test
   fires.
2. How early it fires: the SRM check needs a few thousand users, while the
   outcome test needs tens of thousands for the same experiment. You do not
   wait for the outcome to discover the split is broken.
3. The fix: correct the constant and the same log passes; and the durable
   fix is organizational — the experiment config declares the expected
   ratio, and the platform checks it daily (Fabijan et al., 2019).

The user ids are hashed with crc32, so the assignment is deterministic:
the same id always lands in the same bucket, which is exactly what a
production bucketer must do (Python's built-in hash() is salted per
process and would break reproducibility).
"""

from __future__ import annotations

import math
import zlib

ALPHA = 0.05
EXPECTED_TREATMENT = 0.50


def bucket(user_id: str, threshold: int) -> str:
    """Deterministic bucketing: crc32 % 100 < threshold lands in treatment."""
    h = zlib.crc32(user_id.encode()) % 100
    return "treatment" if h < threshold else "control"


def chi2_sf_1df(chi2: float) -> float:
    """P(X > x) for a chi-square with one degree of freedom, closed form."""
    return math.erfc(math.sqrt(chi2 / 2.0))


def allocation_check(n_users: int, threshold: int) -> tuple[float, float, float, float]:
    """Observed split, chi-square statistic and p-value at this sample size."""
    treat = sum(1 for i in range(n_users) if bucket(f"u{i}", threshold) == "treatment")
    ctrl = n_users - treat
    exp = n_users * EXPECTED_TREATMENT
    chi2 = (treat - exp) ** 2 / exp + (ctrl - exp) ** 2 / exp
    return 100.0 * treat / n_users, chi2, chi2_sf_1df(chi2), treat / ctrl


def users_needed_for_outcome_power(effect: float, alpha: float = 0.05,
                                   power: float = 0.8) -> float:
    """Users per arm for 80% power, outcome sd 1, two-sided t-test."""
    z_alpha = 1.959963984540054
    z_beta = 0.8416212335729143
    return 2.0 * (z_alpha + z_beta) ** 2 / effect**2


def main() -> None:
    print("== 1. the bug: a one-constant drift in the bucket threshold ==")
    print("bucket(user_id): crc32 % 100 < threshold; config declares 50/50.")
    print("the code change moved the threshold 50 -> 52 and the config did not")
    print("follow. The first users see a 52/48 split the experiment believes")
    print("is 50/50.\n")

    print("== 2. the find: the allocation-ratio check at increasing traffic ==")
    print(f"expected treatment share: {100 * EXPECTED_TREATMENT:.0f}%")
    print(f"{'users':>8} {'treat%':>7} {'chi2':>7} {'p':>10}  sr check")
    fired_at = None
    for n in (500, 1000, 2000, 2500, 3000, 4000, 8000, 16000):
        pct, chi2, p, _ = allocation_check(n, 52)
        fired = p < ALPHA
        if fired and fired_at is None:
            fired_at = n
        print(f"{n:>8} {pct:>6.2f}% {chi2:>7.2f} {p:>10.3g}  "
              f"{'FIRES' if fired else 'silent'}")
    print(f"\nsample ratio mismatch fires at {fired_at} users; the outcome test")
    print("has not even reached 10% power there.\n")

    print("== 3. why you cannot wait for the outcome ==")
    per_arm = users_needed_for_outcome_power(effect=0.02)
    print(f"a 2% lift at 80% power needs {per_arm:,.0f} users per arm "
          f"({2 * per_arm:,.0f} total);")
    print(f"the split check fired at {fired_at} -- roughly "
          f"{2 * per_arm / fired_at:.0f}x earlier, on the same traffic.\n")

    print("== 4. the fix: correct the constant, same users, same sessions ==")
    n = 8000
    pct_bad, chi2_bad, p_bad, _ = allocation_check(n, 52)
    pct_good, chi2_good, p_good, _ = allocation_check(n, 50)
    print(f"threshold 52: {pct_bad:.2f}% treatment, chi2={chi2_bad:.2f}, "
          f"p={p_bad:.3g} -> INVALID")
    print(f"threshold 50: {pct_good:.2f}% treatment, chi2={chi2_good:.2f}, "
          f"p={p_good:.3g} -> split restored")
    print("\nThe durable fix is not the constant: the experiment config owns")
    print("the declared ratio, the bucketing code owns the assignment, and a")
    print("daily allocation check (the platform's job, not the analyst's)")
    print("fires on any mismatch -- see Fabijan et al. 2019, KDD.")


if __name__ == "__main__":
    main()
