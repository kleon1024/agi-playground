# Run — when calibration and ranking conflict, executed on the shifted model

**Date:** 2026-08-06
**Command:** `uv run python core/conflict_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

A model can rank clicks perfectly while being miscalibrated. This run
builds such a model and shows the two properties are independent.

## Output

```
  true:      ['0.20', '0.40', '0.60', '0.80']
  predicted: ['0.40', '0.60', '0.80', '1.00']
  ranking match: True
  mean calibration error: 0.20
```

## Notes

- The ranking is identical but every value is wrong by 0.2 — a ranker
  judged only by ordering passes.
- eCPM and the auction (which use the values) inherit the error;
  calibration is a separate property from ranking.
