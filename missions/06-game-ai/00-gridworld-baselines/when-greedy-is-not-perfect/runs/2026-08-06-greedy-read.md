# Run — the greedy baseline's ceiling, read from the recorded baselines run

**Date:** 2026-08-06
**Command:** `uv run python core/greedy_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the committed JSON).
**Cost:** \$0 (local lane; the trials were the stage's recorded 2026-07-31
run).

## Purpose

Stage 00 measured random and greedy baselines. This run reads the record
and asks why greedy is not 100%.

## Output

```
  random  111/500 (0.222) mean 5.43
  greedy  412/500 (0.824) mean 3.15
  board: 5x5, 4 walls, max_steps 12
```

## Notes

- Greedy is one-step lookahead: it can commit to a dead end the step it
  enters, so 82.4% is the ceiling of a policy that cannot see around the
  corner.
- That gap is exactly what a trained policy would have to close.
