# Run — the frame-count axis, read from the recorded 8f and 16f JSONs

**Date:** 2026-08-06
**Command:** `uv run python core/frame_axis.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads six committed seed JSONs).
**Cost:** \$0 (local lane; the training was the stage's recorded 2026-08-01
runs).

## Purpose

Stage 04 doubled stage 02's N_FRAMES from 8 to 16 with the same recipe.
This run reads the recorded JSONs and lays out the axis: quality holds,
exact match gets noisier, cost grows ~4x.

## Output

```
seed 0: 8f mse 0.0804 | 16f mse 0.0818 exact 0.087 cost 567s
seed 1: 8f mse 0.0865 | 16f mse 0.0859 exact 0.140 cost 709s
seed 2: 8f mse 0.0882 | 16f mse 0.0892 exact 0.333 cost 705s

8f mean 0.0851, 16f mean 0.0856
```

## Notes

- Reconstruction quality is unchanged within seed noise (0.0851 vs 0.0856
  mean), but exact-match goes from a 2.7-point seed spread (8f) to a
  24.6-point spread (16f) — a genuinely noisier metric at the harder scale.
- Cost grows ~4x (152.5s to 660s mean) for a 2x frame increase, consistent
  with attention cost growing faster than linear; the tokenizer, not
  compute, remains the binding constraint.
