# Run — the object-count axis, read from the recorded 1-obj and 2-obj JSONs

**Date:** 2026-08-06
**Command:** `uv run python core/object_axis.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads six committed seed JSONs).
**Cost:** \$0 (local lane; the training was the stage's recorded 2026-08-01
runs).

## Purpose

Stage 05 composited two independently-moving shapes while the codec still
emits one token per frame. This run reads the recorded JSONs and lays out
what the second object costs.

## Output

```
seed 0: 1-obj mse 0.0804 | 2-obj mse 0.1429 exact 0.007
seed 1: 1-obj mse 0.0865 | 2-obj mse 0.1486 exact 0.027
seed 2: 1-obj mse 0.0882 | 2-obj mse 0.1533 exact 0.287

1-obj mean 0.0851, 2-obj mean 0.1483
```

## Notes

- The second object costs ~74% more reconstruction MSE (0.0851 -> 0.1483)
  while exact-match collapses to 0.7%-28.7% — the one-token-per-frame
  codec's capacity, not compute, is the binding constraint.
- The stage still closes MET (2-obj mean 0.1483 vs frame-repeat 0.2193,
  margin 6.8x the 0.0104 spread), which is why the verdict reads the
  capacity limit as a finding, not a failure.
