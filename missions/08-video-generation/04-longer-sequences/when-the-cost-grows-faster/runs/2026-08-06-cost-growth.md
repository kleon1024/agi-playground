# Run — the cost growth that outruns the frames, read from the recorded runs

**Date:** 2026-08-06
**Command:** `uv run python core/cost_growth.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads six committed JSONs).
**Cost:** \$0 (local lane; the training was the stage's recorded runs).

## Purpose

Stage 04 doubled N_FRAMES from 8 to 16. This run reads the recorded JSONs
and lays out the cost growth.

## Output

```
  seed 0: 8f 153s, 16f 567s
  seed 1: 8f 151s, 16f 709s
  seed 2: 8f 154s, 16f 705s
  mean 152s -> 660s = 4.3x for a 2x frame count
```

## Notes

- Cost grows ~4x for 2x frames — more than the codec's roughly-linear
  prediction, because the LM's attention cost grows faster than linear too.
- The verdict stays MET (margin 0.0329 vs spread 0.0074), so the axis is a
  cost finding, not a failure.
