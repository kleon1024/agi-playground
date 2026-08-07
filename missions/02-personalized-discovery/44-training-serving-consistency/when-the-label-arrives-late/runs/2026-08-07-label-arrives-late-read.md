# Run — when the label arrives late, executed on the training-cut read

**Date:** 2026-08-07
**Command:** `uv run python core/label_late.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 44's detour: conversions are logged with a delay. This run cuts the
training set at hour 6 and reads what the model estimates for the slow
converters.

## Output

```
label arrives late, read (cut at hour 6, labels need delay):
  item   clicks  total conversions  visible at cut  estimate
  P1001     500              20             20  0.0400 (true 0.0400)
  P1002     400              12              0  0.0000 (true 0.0300)
  P1003     300               9              0  0.0000 (true 0.0300)

reading: P1002 and P1003 converted slowly, so the cut at
hour 6 sees zero of their labels and estimates 0.0000.
The model trains on the fast-converting items only - the
label arrival delay is a sampling bias, and the fix is to
hold out the unconfirmed window, not to trust the cut.
```

## Notes

- P1002 and P1003 converted slowly, so the cut at hour 6 estimates 0.0000 against true rates of 0.0300.
- The label arrival delay is a sampling bias; the fix is to hold out the unconfirmed window, not to trust the cut.
