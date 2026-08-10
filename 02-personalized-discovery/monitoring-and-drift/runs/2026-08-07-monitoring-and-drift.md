# Run — monitoring and drift, executed on the twelve-hour gap trace and slice view

**Date:** 2026-08-07
**Commands:** `uv run python core/drift.py --emit-log /tmp/drift-envelope.json`;
`uv run python prod/slice_drift.py /tmp/drift-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib for `core/`, pandas 3.0.5 for `prod/`.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 47 introduces online monitoring. This run tracks twelve hours of
predicted versus observed CTR and reads when the gap crosses the alert
threshold.

## Output

```
monitoring and drift, read (12 hours, predicted ctr 0.040):
  hour  0: predicted 0.040, observed 0.039, gap 0.001, ewma 0.000
  hour  1: predicted 0.040, observed 0.041, gap -0.001, ewma -0.000
  hour  2: predicted 0.040, observed 0.038, gap 0.002, ewma 0.001
  hour  3: predicted 0.040, observed 0.040, gap 0.000, ewma 0.000
  hour  4: predicted 0.040, observed 0.036, gap 0.004, ewma 0.001
  hour  5: predicted 0.040, observed 0.031, gap 0.009, ewma 0.004
  hour  6: predicted 0.040, observed 0.028, gap 0.012, ewma 0.006
  hour  7: predicted 0.040, observed 0.026, gap 0.014, ewma 0.009
  hour  8: predicted 0.040, observed 0.023, gap 0.017, ewma 0.011
  hour  9: predicted 0.040, observed 0.021, gap 0.019, ewma 0.013
  hour 10: predicted 0.040, observed 0.022, gap 0.018, ewma 0.015 ALERT
  hour 11: predicted 0.040, observed 0.020, gap 0.020, ewma 0.016 ALERT

slice view (same break, confined to a 6% slice):
  homepage    share 90%, observed 0.040 to 0.039
  category-a  share 6%, observed 0.041 to 0.010
  new-users   share 4%, observed 0.040 to 0.033
  aggregate   diluted 0.040 to 0.037

reading: the model kept predicting 0.040 while users
clicked less every hour. The offline eval cannot see this -
its labels come from the same broken world. The prediction-
observation gap, tracked online, is what catches the
regression nobody flagged. Confined to a small slice, the
same break is invisible in the diluted aggregate.
```

## Notes

- The model kept predicting 0.040 while observed CTR fell from 0.039 to 0.020; the EWMA crosses the threshold at hour 10.
- The offline eval cannot see the break — its labels come from the same broken world; the online gap is what catches it.
- The slice view shows the same class of break confined to a 6% slice:
  category-a collapses 0.041 to 0.010 while the diluted aggregate moves
  0.040 to 0.037, which is the case the `prod/slice_drift.py` panel
  exists to catch.
