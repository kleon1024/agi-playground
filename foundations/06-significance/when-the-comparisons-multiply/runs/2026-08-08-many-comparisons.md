# Run — twelve comparisons, declared alpha, and the false positives

**Date:** 2026-08-08
**Command:** `uv run python core/many_comparisons.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.6s.
**Cost:** \$0 (local lane).

## Purpose

The significance chapter compares two models with one declared alpha. This
run measures what happens when the same alpha is applied to 12 independent
paired comparisons at once: the comparisons that fire by chance, the
family-wise probability behind them, and what Benjamini-Hochberg false
discovery rate control changes — including what it costs.

## Output

```
null experiment: all 12 pairs have true effect zero, one draw, n=300 items each
  naive alpha=0.05 flags 1 of 12 by chance
  expected under the null: 0.6; P(at least one) = 1 - 0.95^12 = 46.0%
  BH q=0.1 flags 1 of 12

planted experiment: pair 6 carries true effect 0.25, one draw
  pair    p-value   naive  BH q=0.10  true?
     0     0.6406    keep       keep  False
     1     0.2962    keep       keep  False
     2     0.0937    keep       keep  False
     3     0.0255  reject       keep  False
     4     0.2327    keep       keep  False
     5     0.4776    keep       keep  False
     6   5.19e-07  reject     reject  True
     7     0.3607    keep       keep  False
     8     0.4340    keep       keep  False
     9     0.0170  reject       keep  False
    10     0.7123    keep       keep  False
    11     0.0513    keep       keep  False
  naive rejects 3; BH rejects 1

500 experiments, planted shape (11 null + 1 true):
  mean false positives per experiment: naive 0.59 vs BH 0.22
  share of experiments with at least one false positive (naive): 44.2% (theory for 11 nulls: 43.1%)
  share of experiments with at least one false positive (BH): 16.8%
  true pair missed: naive 6/500, BH 25/500
  verdict: naive fires ~0.6 false positives per experiment; BH q=0.10
  cuts that to ~0.22 while keeping the planted effect almost always.
```

## Reading the output

- **The null experiment shows the family-wise probability.** With all 12
  pairs truly null, the single draw flags 1 of 12 at alpha 0.05 — the
  expected count is 0.6, and the probability that at least one of 12 fires
  is 1 - 0.95^12 = 46.0 percent. One comparison at alpha 0.05 lies 5
  percent of the time; twelve comparisons lie almost half the time.
- **The planted draw shows the fix at work.** Pair 6 carries the real
  effect (p = 5.19e-07). Naive testing also rejects pairs 3 and 9 (p =
  0.0255, 0.0170) — two chance hits that look like wins. BH at q = 0.10
  rejects only pair 6: the chance hits sit below the rank-scaled threshold
  and are suppressed.
- **Repetition measures the trade, not just the one draw.** Across 500
  experiments BH cuts mean false positives from 0.59 to 0.22 per
  experiment and the share of experiments with at least one false positive
  from 44.2 percent to 16.8 percent. It pays for that: the true pair is
  missed 25/500 times versus 6/500 for naive testing, because BH's
  threshold for the top-ranked test (q/m = 0.0083) is stricter than the
  per-test alpha of 0.05 — a real, small power cost, not a rounding
  artifact.

## Notes

- Paired z-tests on synthetic per-item differences (n=300 per pair), one
  planted pair with true effect 0.25 per-item standard deviation, fixed
  seed 39: re-running reproduces these exact numbers.
- Benjamini-Hochberg implemented as the step-up procedure on sorted
  p-values (Benjamini & Hochberg, 1995, JRSS-B, doi
  10.1111/j.2517-6161.1995.tb02031.x): reject all tests with rank at or
  below the largest rank k whose p-value is at most k*q/m.
