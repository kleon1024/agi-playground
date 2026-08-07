# Run — when the second model costs, executed on the temperature-scaled head

**Date:** 2026-08-07
**Command:** `uv run python core/calibration_layer.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 2.3s (fit + shifted reads).
**Cost:** \$0 (local lane).

## Purpose

The stage-64 audit shows the naive click head's calibration slope at 1.188.
This detour repairs the mapping with temperature scaling and measures the
second model's real cost: the calibrated head is only as fresh as its
re-fit cadence, and a distribution shift breaks the frozen temperature.

## Output

```
when the second model costs, read (temperature scaling):
  fitted T: 0.85
  read                          slope intercept
  raw scores                    1.098    -0.067
  temperature-scaled            0.983    -0.009
  shifted, raw                  1.097    -0.165
  shifted, stale T              0.980    -0.106

reading: the raw ranking score is not a probability (slope off
1.0), and temperature scaling repairs the mapping on the split
it was fitted on. the layer is a second model with its own
freshness: a distribution shift breaks the frozen T, so the
calibration must be re-fitted or monitored, and the cost is
operational -- a monitoring job, a re-fit cadence, and a
handoff to every pCTR consumer.
```

## Notes

- Temperature scaling (Guo et al., ICML 2017, arXiv:1706.04599) moves the
  slope from 1.098 to 0.983 and the intercept from -0.067 to -0.009 on
  the split it was fitted on.
- After a shift, the raw scores' intercept moves (-0.067 to -0.165) and
  the stale fitted T is wrong for the new distribution (intercept -0.106
  instead of -0.009): calibration is a second model with its own
  freshness cost, not a one-time fix.
- The operational cost is the re-fit cadence, a monitoring job on the
  slope/intercept pair, and a handoff to every pCTR consumer — the same
  ownership shape as stage 46's retraining/staleness loop.
