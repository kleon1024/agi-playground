# Run — when the score is on the surface, executed on the calibration read

**Date:** 2026-08-07
**Command:** `uv run python core/surface_score.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 41 selects creative by score. This run compares surface scores with measured CTR.

## Output

```
surface score, read:
  'Buy now': surface 0.9, measured CTR 0.02
  'Run faster, pay less': surface 0.7, measured CTR 0.08
  'Marathon shoes, 20% off': surface 0.6, measured CTR 0.06
  surface winner: 'Buy now'
  CTR winner:     'Run faster, pay less'

reading: the surface score rewards urgency ('Buy now'), the
measured CTR rewards specificity. A launch that trusts the
surface score ships the wrong creative — the score has to be
calibrated against real delivery before it decides.
```

## Notes

- The surface score rewards urgency ('Buy now'), the measured CTR rewards specificity.
- A launch that trusts the surface score ships the wrong creative — the score has to be calibrated against real delivery before it decides.
