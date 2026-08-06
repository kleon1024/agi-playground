# Run — the compounding axes, read from the recorded fourth-corner run

**Date:** 2026-08-06
**Command:** `uv run python core/axes_compound.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads three committed JSONs).
**Cost:** \$0 (local lane; the training was the stage's recorded 2026-08-05
runs).

## Purpose

Stage 06 ran both axes together: 16 frames and 2 objects. This run reads
the recorded JSONs and lays out where the difficulties compound.

## Output

```
  seed 0: lm 0.1391 vs baseline 0.1998, exact 0.0000, verdict MET
  seed 1: lm 0.1375 vs baseline 0.1998, exact 0.0067, verdict MET
  seed 2: lm 0.1456 vs baseline 0.1998, exact 0.0067, verdict MET
```

## Notes

- In pixel space the axes do not add (MSE inside the range the second
  object alone cost); in token space exact-match collapses to near zero.
- The one-token-per-frame capacity is the binding constraint, and the
  verdict still closes MET at 22-27% of the ceiling.
