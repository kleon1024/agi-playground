# Run — the flipped variance, read from the recorded real-photo fusion run

**Date:** 2026-08-06
**Command:** `uv run python core/flip_variance_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the committed JSON).
**Cost:** \$0 (local lane; the training was the stage's recorded 2026-08-01
runs).

## Purpose

Stage 04's real-photo result flipped the variance structure. This run reads
the recorded JSON and lays out the per-seed numbers.

## Output

```
  vision:    [0.2374, 0.2424, 0.2323]  spread 0.0101
  text-only: [0.2121, 0.1919, 0.2626]  spread 0.0707
  margin: +0.0152
```

## Notes

- The noise flipped arms: text-only is now 7x noisier (0.0707 vs 0.0101),
  the opposite of stage 01's synthetic case.
- The narrow margin belongs to a stable vision pathway, not two equally
  noisy ones.
