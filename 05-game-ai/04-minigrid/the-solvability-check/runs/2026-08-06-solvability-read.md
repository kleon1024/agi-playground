# Run — the solvability check, read from the recorded MiniGrid run

**Date:** 2026-08-06
**Command:** `uv run python core/solvability_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the training was the stage's recorded 2026-08-01
runs).

## Purpose

Stage 04's cold-start result is only meaningful if the task is solvable.
This run reads the recorded checks and lays out the two proofs and the
random floor.

## Output

```
  hand-scripted 9-action sequence reaches the goal (seeds 0-4)
  run_wall_follow: 500/500 = 100% success
  run_random: 2/500 = 0.4% success
```

## Notes

- The task is solvable (100% under wall-following), so a cold-start
  failure is the training, not the environment.
- The solvability check is what makes the null result attributable.
