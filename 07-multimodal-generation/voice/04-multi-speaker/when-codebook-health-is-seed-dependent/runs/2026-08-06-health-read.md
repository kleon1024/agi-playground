# Run — the seed-dependent codebook health, read from the recorded run

**Date:** 2026-08-06
**Command:** `uv run python core/health_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads three committed JSONs).
**Cost:** \$0 (local lane; the training was the stage's recorded 2026-08-01
runs).

## Purpose

Stage 04's 10-speaker retrain showed no full collapse, but codebook health
became seed-dependent. This run reads the JSONs and lays out the spread.

## Output

```
  seed 0: codes 18/64, entropy ratio 0.405, eval MSE 0.02712
  seed 1: codes 63/64, entropy ratio 0.760, eval MSE 0.01698
  seed 2: codes 32/64, entropy ratio 0.644, eval MSE 0.02122
```

## Notes

- No collapse in any seed, but the 18-vs-63 code spread is seed-dependent
  — the same recipe that escaped reliably at 1-2 speakers no longer does
  at 10.
- That fix-generalization gap is what stage 04 records and stage 05's
  reset targets.
