# Run — pCTR calibration, executed on the stage's miscalibrated estimate

**Date:** 2026-08-06
**Command:** `uv run python core/ctr_calibration.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Ad ranking uses pCTR inside eCPM, so a miscalibrated estimate corrupts the
auction. This run measures the calibration error on a systematically
overestimating model.

## Output

```
  predicted range 0.50-0.59, observed clicks 3/10
  ECE = 0.2450
```

## Notes

- The model predicts ~0.55 but only ~0.3 of these actually click — a
  systematic overestimate.
- Inside eCPM this inflates the ad's revenue estimate, so it wins the
  auction too often. ECE is the number that catches it.
