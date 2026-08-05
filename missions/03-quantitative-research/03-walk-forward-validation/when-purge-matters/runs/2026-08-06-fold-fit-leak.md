# Run — per-fold selection, the boundary regime, and the purge null

**Date:** 2026-08-06
**Command:** `uv run python core/fold_fit_leak.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only (plus the stage 00 AAPL
fetch).
**Software:** Python 3.11.14 via uv; stdlib only; reuses the stage's
`walk_forward.py` importably.
**Wall-clock:** 0.5s.
**Cost:** \$0 (local lane).

## Purpose

The stage's recorded run found no leakage uplift for a fixed linear rule and
said so explicitly. This run gives the fold real selection power — a grid of
thresholds per fold, kept by in-fold Sharpe — and measures two things: the
gap between in-fold and out-of-fold Sharpe (fold-specific fit is not strategy
fit), and the boundary regime (the first label-days test rows of every block,
whose labels overlap the training window when unpurged).

## Output (key lines)

```
### label days = 5
== chronological, unpurged ==
  fold 0: chosen +0.000  in-fold 0.466  out-of-fold 1.703
  fold 2: chosen -0.020  in-fold 0.618  out-of-fold 0.015
  aggregate out-of-fold Sharpe: 0.9309
  boundary rows (25): Sharpe 3.1706  |  interior rows (590): Sharpe 0.8451
== purged + gapped ==
  aggregate out-of-fold Sharpe: 1.1287
  boundary rows (25): Sharpe 3.1706  |  interior rows (590): Sharpe 1.0501

### label days = 20
== chronological, unpurged ==
  aggregate out-of-fold Sharpe: 2.1243
  boundary rows (100): Sharpe 0.6547  |  interior rows (507): Sharpe 2.4130
== purged + gapped ==
  aggregate out-of-fold Sharpe: 2.1476
  boundary rows (100): Sharpe 0.6547  |  interior rows (507): Sharpe 2.4416
```

## Notes

- **Fold-specific fit is not strategy fit, measured.** In-fold Sharpe runs
  0.47-0.63 (5-day labels) and 1.02-1.40 (20-day labels) while the same
  fold's out-of-fold Sharpe runs 0.015-1.88 and -1.06-3.74. The in-fold
  number never predicts the out-of-fold number; the per-fold selector is
  choosing a threshold the fold has already seen.
- **The boundary is a different regime.** The first label-days test rows of
  every block score 3.17 vs 0.85 interior (5-day) and 0.65 vs 2.41 interior
  (20-day) — systematically different in both directions. The boundary
  artifact is real and measurable even when the aggregate is not.
- **The purge null, stated plainly.** On AAPL with this momentum rule,
  purge+gap did not inflate the aggregate: 0.93 vs 1.13 (5-day) and 2.12 vs
  2.15 (20-day), both within fold noise and consistent with the stage's
  recorded run. The overlap is real (the boundary rows prove it exists), but
  this signal does not exploit it. A demonstration that purge "fixed" an
  uplift that was never observed would be a fabricated win; the chapter
  reports the null and the boundary measurement instead.
