# Run — when the alert is noisy, executed on the threshold sweep

**Date:** 2026-08-07
**Command:** `uv run python core/noisy_alert.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 47's detour: observed CTR jitters around the prediction. This run
alarms on a declared break at hour 8 under three thresholds and reads the
false-alarm trade.

## Output

```
alert is noisy, read (predicted ctr 0.040, break at hour 8):
  threshold +/-0.002: alerts at hours [2, 3, 7, 8, 9, 10, 11]
  threshold +/-0.005: alerts at hours [8, 9, 10, 11]
  threshold +/-0.010: alerts at hours [9, 10, 11]

reading: at +/-0.002 the panel fires on seven hours of noise;
at +/-0.010 it waits until the break is unmistakable. The
threshold is a decision about what a false alarm costs and
how fast a real break must be caught - it cannot be both
tight and quiet.
```

## Notes

- At +/-0.002 the panel fires on seven hours, including jitter at hours 2, 3, and 7; at +/-0.010 it misses hour 8.
- The threshold is a decision about what a false alarm costs and how fast a real break must be caught — it cannot be both tight and quiet.
