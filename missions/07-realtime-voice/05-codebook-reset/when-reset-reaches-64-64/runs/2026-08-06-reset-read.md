# Run — the 64/64 reset, read from the recorded codebook-reset run

**Date:** 2026-08-06
**Command:** `uv run python core/reset_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads three committed JSONs).
**Cost:** \$0 (local lane; the training was the stage's recorded 2026-08-01
runs).

## Purpose

Stage 05 applied a dead-code reset and reached full utilization in every
seed. This run reads the JSONs and lays out the before/after.

## Output

```
  seed 0: codes 64/64, entropy ratio 0.826, resets 1893
  seed 1: codes 64/64, entropy ratio 0.814, resets 1848
  seed 2: codes 64/64, entropy ratio 0.791, resets 1388
```

## Notes

- The reset reaches 64/64 in every seed (vs stage 04's 18/63/32) — the
  mechanism fixes utilization.
- Whether it or the EMA update did the work is stage 06's factorial
  question.
