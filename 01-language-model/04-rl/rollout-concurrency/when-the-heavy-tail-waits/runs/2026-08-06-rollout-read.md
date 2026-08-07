# Run — the heavy tail that waits, read from the recorded scheduling JSON

**Date:** 2026-08-06
**Command:** `uv run python core/rollout_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the committed JSON).
**Cost:** \$0 (local lane; the scheduling was the chapter's recorded
2026-08-02 run).

## Purpose

The rollout-concurrency chapter fed the same 40-trajectory list to lockstep
and async policies at 2, 4, 8 workers. This run reads the JSON and lays
out the reading.

## Output

```
lockstep vs async rollout scheduling (recorded), read:
  workers 2: lockstep 0.0395s  async 0.0229s  speedup 1.73x
  workers 4: lockstep 0.0307s  async 0.0207s  speedup 1.48x
  workers 8: lockstep 0.0263s  async 0.0203s  speedup 1.30x
```

## Notes

- The same trajectory list in both policies, alternating trial order: the
  only difference is the scheduling policy.
- Async wins at every worker count because a finished worker grabs the
  next rollout instead of waiting on the heavy-tailed long episodes — the
  speedup narrows as workers increase (1.73x to 1.30x) because the wait is
  shorter with more parallelism, but the tail never disappears.
