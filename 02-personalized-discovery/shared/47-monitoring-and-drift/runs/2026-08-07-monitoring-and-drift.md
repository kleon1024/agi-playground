# Run — monitoring and drift, executed on the twelve-hour gap trace

**Date:** 2026-08-07
**Command:** `uv run python core/drift.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
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

reading: the model kept predicting 0.040 while users
clicked less every hour. The offline eval cannot see this -
its labels come from the same broken world. The prediction-
observation gap, tracked online, is what catches the
regression nobody flagged.
```

## Notes

- The model kept predicting 0.040 while observed CTR fell from 0.039 to 0.020; the EWMA crosses the threshold at hour 10.
- The offline eval cannot see the break — its labels come from the same broken world; the online gap is what catches it.
