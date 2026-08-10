# Run — ads measurement, executed on the incrementality model

**Date:** 2026-08-07
**Command:** `uv run python core/incrementality.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 30 asks what an ad actually changed. This run compares an exposed
group's conversion rate against a control and reads the lift.

## Output

```
incrementality, read:
  exposed: 0.032 conversion rate
  control: 0.028
  lift:    14.3%

reading: the ad's raw clicks overstate its effect — 0.028 of
the exposed users would have converted anyway. The increment is
0.4 points, the part the ad actually caused. Attribution that
ignores the control group credits the ad with the baseline.
```

## Notes

- The exposed group converts at 0.032, but 0.028 of that would have
  happened without the ad; the increment is 0.4 points (14.3% lift).
- Attribution without a control group credits the ad with the
  baseline, which is the overcount the detour measures.
