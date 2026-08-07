# Run — when the join looks ahead, executed on the training-join read

**Date:** 2026-08-07
**Command:** `uv run python core/join_lookahead.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 44's detour: the training joiner snaps each label to the feature
snapshot taken at label arrival instead of at decision time. The snapshot
then contains clicks that happened after the decision, including the
conversions the label counts. This run reads the two training tables the
two join strategies produce and what each lets the model conclude.

## Output

```
join looks ahead, read (clicks at hour 2, labels arrive hour 5):
  training rows as joined by each strategy:
  as-of join (snapshot at decision hour 2):
    P1001: item_ctr 0.020, label ctr 0.020
    P1002: item_ctr 0.020, label ctr 0.020
  label-time join (snapshot at hour 5):
    P1001: item_ctr 0.024, label ctr 0.020
    P1002: item_ctr 0.020, label ctr 0.020

  offline separation, leaked join: 1.00
  offline separation, as-of join:   0.00

reading: the label-time snapshot contains the outcome's own
window: P1001's early conversions raised its feature from
0.020 to 0.024, so the leaked join 'predicts' the label from
the label. The as-of join returns the honest answer - both
items were identical at decision time, so there is nothing
to rank on. A leak that looks like signal offline is how a
model learns to promote its own luck.
```

## Notes

- The as-of join is the discipline stage 43's store encodes for serving;
  this run shows the same discipline on the training side: the feature
  snapshot must be the one a serving read at decision time would have
  returned, not the one at label arrival.
- A leaked join does not look broken: it separates the training rows
  perfectly, so the offline eval endorses it. The tell is that the
  feature could not have been known at decision time — which is why
  leakage checks inspect feature timestamps, not holdout scores.
