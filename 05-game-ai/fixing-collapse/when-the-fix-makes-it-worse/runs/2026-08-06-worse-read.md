# Run — the fix that made it worse, read from the recorded collapse sweep

**Date:** 2026-08-06
**Command:** `uv run python core/worse_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the training was the stage's recorded 2026-08-01
runs).

## Purpose

Stage 03 tried two fixes for the collapse. This run reads the recorded
sweep and lays out the per-variant results.

## Output

```
  baseline (group_size=8): 0.078/0.062/0.078 greedy
  small-group (group_size=4): 0.024/0.050/0.036 greedy
  entropy-bonus (coef=0.01): 0.078 greedy
```

## Notes

- Both fixes failed; small-group made the collapse strictly worse
  (single-character L-then-EOS completions on every example).
- A recorded null that says the training signal, not the group size, is
  the wall.
