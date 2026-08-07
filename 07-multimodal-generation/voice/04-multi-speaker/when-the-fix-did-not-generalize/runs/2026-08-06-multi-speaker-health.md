# Run — codebook health at 10 speakers, three seeds

**Date:** 2026-08-06
**Command:** `uv run python core/multi_speaker_health.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads three recorded JSONs).
**Cost:** \$0 (local lane; the underlying training was the stage's recorded
run).

## Purpose

Stage 04 retrains the codec at 10 speakers to test whether the 1-2 speaker
fix generalizes. This run reads the three seeds' final codebook usage and
reconstruction MSE and lays out the seed-dependent health the stage found.

## Output

```
seed  codes  entropy      MSE
   0   18/64    0.405   0.0271
   1   63/64    0.760   0.0170
   2   32/64    0.644   0.0212
```

## Notes

- At 10 speakers the codebook health is seed-dependent again: seed 1 is
  healthy (63/64), seed 0 is collapsed (18/64), seed 2 partial (32/64).
  The 1-2 speaker fix did not generalize — the same seed-dependence the
  codebook chapters measured at 1-2 speakers returns at the frontier.
- Reconstruction MSE tracks usage (0.027 at 18/64, 0.017 at 63/64): the
  collapsed codebook's cost is measurable, not just a usage count.
