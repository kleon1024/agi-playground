# Run — the slice-aware drift panel over the emitted trace

**Date:** 2026-08-07
**Commands:** `uv run python core/drift.py --emit-log /tmp/drift-envelope.json`;
`uv run python prod/slice_drift.py /tmp/drift-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib for `core/`, pandas 3.0.5 for `prod/`.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 47's gap panel catches a break that moves the aggregate. This run
is the case-finding half of the stage: the break that does not move the
aggregate, because it is confined to a small traffic segment. The core
script emits the hourly trace plus per-slice observed series; the
production panel applies the same EWMA gap check per slice and names the
segment that crossed the threshold while the diluted aggregate stayed
under it.

## Output

```
slice-aware drift panel (predicted 0.040, threshold 0.010):
  slice        share        observed    gap  alert
  aggregate    diluted  0.040 -> 0.037  0.003  never
  homepage         90%  0.040 -> 0.039  0.001  never
  category-a        6%  0.041 -> 0.010  0.030  hour 10
  new-users         4%  0.040 -> 0.033  0.007  never

verdict: HIDDEN SLICE -- the aggregate stayed under threshold
while category-a crossed it. The break is confined to a small
traffic segment; the page-level panel cannot see it. Slice-
aware thresholds per segment are the fix, not a tighter
aggregate threshold.
```

## Notes

- Category-a carries the price feature that breaks at hour 5; its
  observed CTR collapses 0.041 to 0.010 and the EWMA gap crosses the
  threshold at hour 10. The 90% homepage slice stayed flat, so the
  diluted aggregate moved only 0.003 and never alerted.
- The panel's message is the stage's: a flat aggregate is not proof the
  page is fine — it is a promise to slice. The drift taxonomy Gama et
  al. survey applies per slice ("A Survey on Concept Drift Adaptation",
  ACM Computing Surveys, 2014).
