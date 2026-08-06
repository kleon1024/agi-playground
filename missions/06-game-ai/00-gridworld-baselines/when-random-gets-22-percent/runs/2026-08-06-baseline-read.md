# Run — the two baselines, read from the committed JSON

**Date:** 2026-08-06
**Command:** `uv run python core/baseline_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the committed baselines JSON).
**Cost:** \$0 (local lane; the underlying trials were the stage's recorded
2026-07-31 run).

## Purpose

Stage 00's recorded baselines.json holds the two numbers a trained policy
must clear. This run reads it and lays out what each baseline measures —
including why random is not near zero on a mostly-open 5x5 board.

## Output

```
gridworld: 5x5, 4 walls, 500 trials per baseline
  random  111/500 (0.222)  mean 5.43 steps
  greedy  412/500 (0.824)  mean 3.15 steps
```

## Notes

- Random solves 22.2% of boards: on a mostly-open 5x5 grid with only four
  walls, a persistent random walk reaches the goal a non-trivial share of
  the time. The no-learning floor is a real number, not a near-zero.
- Greedy one-step lookahead solves 82.4% in fewer steps (3.15 vs 5.43 mean):
  the bar that actually separates trained from untrained policy.
