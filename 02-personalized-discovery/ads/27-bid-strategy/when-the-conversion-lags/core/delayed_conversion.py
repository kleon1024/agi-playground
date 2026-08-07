"""The delayed-conversion detour: a label that has not arrived yet
reads as a negative.

Stage 27 derives the bid from the conversion rate. The conversion is
not observed at click time — it arrives after a delay, so at any
snapshot the freshest clicks are the most likely to still be in
flight. Labeling them negative because they have not converted yet
under-reads CVR, and the target-CPA bid underbids. This script
simulates 100,000 clicks (fixed seed) over a seven-day snapshot with
true CVR 0.02 and a lognormal conversion delay (median three days),
and compares the naive label against the delay-corrected soft label.

Run:
    uv run python core/delayed_conversion.py
"""

from __future__ import annotations

import math
import random

N_CLICKS = 100_000
TRUE_CVR = 0.02
CONVERSION_VALUE = 5.0
WINDOW_DAYS = 7.0
DELAY_MEDIAN = 3.0
DELAY_SIGMA = 1.0


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def delay_cdf(days: float) -> float:
    """P(delay <= days) for lognormal(median, sigma)."""
    if days <= 0:
        return 0.0
    return norm_cdf((math.log(days) - math.log(DELAY_MEDIAN)) / DELAY_SIGMA)


def main() -> None:
    rng = random.Random(20260808)

    naive_sum = 0.0
    corrected_sum = 0.0
    for _ in range(N_CLICKS):
        # Age of the click at snapshot, uniform over the seven-day window.
        age = WINDOW_DAYS * rng.random()
        converts = rng.random() < TRUE_CVR
        if converts:
            # Lognormal delay; median three days.
            delay = DELAY_MEDIAN * math.exp(DELAY_SIGMA * rng.gauss(0, 1))
            converted_by_now = delay <= age
        else:
            converted_by_now = False
        f_age = delay_cdf(age)
        # Naive label: converted by now, else a hard negative.
        naive_sum += 1.0 if converted_by_now else 0.0
        # Corrected label: converted by now, else the probability the
        # click still converts given it has not converted by age a —
        # Chapelle's fake-negative correction.
        if converted_by_now:
            corrected_sum += 1.0
        else:
            denom = 1.0 - TRUE_CVR * f_age
            corrected_sum += TRUE_CVR * (1.0 - f_age) / denom

    naive_cvr = naive_sum / N_CLICKS
    corrected_cvr = corrected_sum / N_CLICKS

    print("delayed-conversion audit: 100,000 clicks, fixed seed")
    print("true CVR 0.02; conversion delay lognormal, median 3 days")
    print("seven-day snapshot; clicks aged uniformly 0 to 7 days\n")
    print(f"  {'CVR read':>18} {'CVR':>8} {'bid ($5 x CVR)':>15}")
    print(f"  {'true':>18} {TRUE_CVR:>8.4f} {CONVERSION_VALUE * TRUE_CVR:>15.2f}")
    print(f"  {'naive (hard negatives)':>18} {naive_cvr:>8.4f} "
          f"{CONVERSION_VALUE * naive_cvr:>15.2f}")
    print(f"  {'delay-corrected':>18} {corrected_cvr:>8.4f} "
          f"{CONVERSION_VALUE * corrected_cvr:>15.2f}")
    underread = 1.0 - naive_cvr / TRUE_CVR
    print(f"\nnaive under-read: {underread:.0%} of the true CVR")
    print("  -> target-CPA bid drops from $0.10 to "
          f"${CONVERSION_VALUE * naive_cvr:.2f}")

    print("\nreading: a conversion that arrives tomorrow is labeled a")
    print("negative today. Fresh clicks carry most of the in-flight mass,")
    print("so the naive model under-reads CVR and the bid underbids — the")
    print("advertiser loses the auctions it should have won. The fix is a")
    print("joint fit of conversion and delay (Chapelle 2014): each not-")
    print("yet-converted click gets the probability it still converts,")
    print("not a hard zero.")


if __name__ == "__main__":
    main()
