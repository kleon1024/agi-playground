# Run — the 34-second loss curve, read from the recorded run

**Date:** 2026-08-06
**Command:** `uv run python core/curve_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the underlying training was the chapter's
recorded 2026-07-26 GPU run).

## Purpose

The first training loop's recorded run holds the train/val loss at every
250-iteration checkpoint. This run reads that record and lays out the two
halves of the curve — the fast descent and the growing train/val gap.

## Output

```
iter   train     val     gap
    0   4.327   4.327  +0.001
  250   2.538   2.545  +0.007
  500   2.037   2.095  +0.058
  750   1.654   1.811  +0.157
 1000   1.482   1.664  +0.182
 1250   1.385   1.605  +0.220
 1500   1.327   1.570  +0.243
 1750   1.284   1.545  +0.260
 2000   1.275   1.538  +0.263
```

## Notes

- The loop learns fast (val 4.327 -> 1.538 in 2000 iterations, 34.2s), and
  the train/val gap grows monotonically from +0.001 to +0.263 — the descent
  and the overfitting are the same curve, read at different times.
- The gap is a diagnostic, not a failure: 2000 iterations on 1.1MB of text
  is a toy that has memorized its training set by the end.
