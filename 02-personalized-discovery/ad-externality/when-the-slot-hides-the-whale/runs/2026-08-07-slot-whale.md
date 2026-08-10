# Run — the whale-slot distribution audit

**Date:** 2026-08-07
**Command:** `uv run python core/slot_whale.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

The stage audit reports average displacement. This read asks the
follow-up: what does the distribution look like when a slate contains one
exceptionally valuable organic item — a breaking story, the product the
user was searching for? It draws 10,000 impressions (fixed seed): in 90
percent the whale ranks above the ad's slot and displacement is small; in
10 percent the whale is the marginal item the ad displaces. It reports
the mean and the tail of the displacement distribution.

## Output

```
whale-slot read: 10,000 impressions; one slate in ten carries a
0.95 whale at the ad's position

          metric    value
         average   0.2307
             P50   0.1557
             P90   0.9500
             P99   0.9500
     max (whale)   0.9500
```

## Notes

- The average displacement is 0.2307, the median 0.1557 — routine slots
  dominate the mean. P90 and P99 are both 0.9500: one slate in ten, the
  ad displaces the user's single most valuable result, more than four
  times the average.
- An externality decision made on the average prices the routine slots
  and ignores the tail, which is exactly where the long-term value is.
  The tail quantile, not the mean, is the decision number.
- Values drawn with a fixed seed; illustrative and deterministic, not
  measured organic-value loss per position.
