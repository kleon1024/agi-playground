# Run — the collapsed policy, read from the three recorded GRPO seeds

**Date:** 2026-08-06
**Command:** `uv run python core/collapse_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads three committed seed JSONs).
**Cost:** \$0 (local lane; the training was the stage's recorded 2026-07-31
runs).

## Purpose

Stage 01's recorded seeds hold the mission's null result: every trained seed
collapses to a constant direction string and greedy-decoded success sits far
below both baselines. This run reads the JSONs and lays out the collapse.

## Output

```
seed 0: greedy success 0.078 | emits 'RRRRRR...' on all held-out boards
seed 1: greedy success 0.062 | emits 'UUUUUU...' on all held-out boards
seed 2: greedy success 0.078 | emits 'LLLLLL...' on all held-out boards
```

## Notes

- Each seed emits one constant direction string (12 repeats) on every
  held-out board — the policy did not learn to navigate, it learned to emit
  a fixed action and stop.
- Greedy success (0.062-0.078) is far below both stage 00 baselines
  (random 0.222, greedy 0.824), which is why the mission's report is an
  honest null rather than a partial win.
