# Run — the shuffle that did not move the score, read from the record

**Date:** 2026-08-06
**Command:** `uv run python core/shuffle_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the walk-forward run was the stage's recorded).

## Purpose

Stage 03 compared shuffled, chronological-unpurged, and purged walk-forward
evaluation. This run reads the record and lays out the three paths and the
negative result.

## Output

```
  shuffled-invalid out-of-fold Sharpe 0.7393
  chronological-unpurged 0.9722
  purged-five-day/gapped-five-day 0.9722
  14-trial teaching deflation was 0.3145
```

## Notes

- This rule's score is the same with and without purge because the
  recovered implementation never used its training indices — a negative
  result, not proof leakage is harmless.
- The comparison is the point, not the number: a different rule could leak,
  and the three paths are what make the difference legible.
