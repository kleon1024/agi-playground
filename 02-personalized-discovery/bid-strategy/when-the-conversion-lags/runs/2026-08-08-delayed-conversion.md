# Run — the delayed-conversion audit

**Date:** 2026-08-08
**Command:** `uv run python core/delayed_conversion.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.09s.
**Cost:** \$0 (local lane).

## Purpose

The stage run derives the bid from the conversion rate. The conversion
is not observed at click time — it arrives after a delay, so at any
snapshot the freshest clicks are the most likely to still be in flight.
Labeling them negative because they have not converted yet under-reads
CVR and the target-CPA bid underbids. This script simulates 100,000
clicks (fixed seed) over a seven-day snapshot with true CVR 0.02 and a
lognormal conversion delay (median three days), and compares the naive
label against the delay-corrected soft label.

## Output

```
delayed-conversion audit: 100,000 clicks, fixed seed
true CVR 0.02; conversion delay lognormal, median 3 days
seven-day snapshot; clicks aged uniformly 0 to 7 days

            CVR read      CVR  bid ($5 x CVR)
                true   0.0200            0.10
  naive (hard negatives)   0.0096            0.05
     delay-corrected   0.0197            0.10

naive under-read: 52% of the true CVR
  -> target-CPA bid drops from $0.10 to $0.05

reading: a conversion that arrives tomorrow is labeled a
negative today. Fresh clicks carry most of the in-flight mass,
so the naive model under-reads CVR and the bid underbids — the
advertiser loses the auctions it should have won. The fix is a
joint fit of conversion and delay (Chapelle 2014): each not-
yet-converted click gets the probability it still converts,
not a hard zero.
```

## Notes

- The naive model reads 0.0096 — 52 percent under the true 0.02 — and
  the target-CPA bid falls from \$0.10 to \$0.05. A conversion that
  arrives tomorrow is labeled a negative today, and fresh clicks carry
  most of the in-flight mass.
- The delay-corrected soft label recovers 0.0197: each not-yet-
  converted click is labeled with the probability it still converts
  given its age, the joint conversion-and-delay model of Chapelle
  (KDD 2014). The bid returns to \$0.10.
- Same failure family as the recommendation track's delayed-feedback
  stage (57), where a young snapshot under-reads fresh traffic. Ages
  uniform over the window, delays lognormal, conversions Bernoulli,
  fixed seed. Illustrative and deterministic, not real bid logs.
