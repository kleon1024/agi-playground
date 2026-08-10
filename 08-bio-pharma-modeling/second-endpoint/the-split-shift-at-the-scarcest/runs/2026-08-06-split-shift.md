# Run — the split shift at the scarcest endpoint, read from the record

**Date:** 2026-08-06
**Command:** `uv run python core/split_shift.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the committed split summary).
**Cost:** \$0 (local lane; the split was the stage's recorded run).

## Purpose

Stage 03's NR-PPAR-gamma split shifts the positive rate sharply. This run
reads the split summary and lays out the shift beside the verdict.

## Output

```
  n_train 5154 n_test 1289, scaffold overlap 0
  train positive 2.29% vs test 5.28% (shift 2.3x)
```

## Notes

- The scarcest endpoint carries the largest split shift: with 118 train
  positives, whole-scaffold assignment moves a larger fraction of the
  minority class.
- The shift is the same confound the inconclusive verdict's variance
  measures.
