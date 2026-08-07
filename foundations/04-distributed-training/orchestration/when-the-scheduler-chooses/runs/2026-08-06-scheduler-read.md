# Run — the scheduler that chooses whose work waits, read from the recorded JSON

**Date:** 2026-08-06
**Command:** `uv run python core/scheduler_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the committed JSON).
**Cost:** \$0 (local lane; the scheduling was the chapter's recorded
2026-08-01 run).

## Purpose

The orchestration chapter compared FIFO and priority scheduling on two
slots. This run reads the recorded JSON and lays out the reading: makespan
is unchanged; whose work waits is the entire difference.

## Output

```
FIFO vs priority (recorded), read:
  fifo      makespan 0.0182s | hi-priority wait 0.0074s | lo-priority wait 0.0074s
  priority  makespan 0.0187s | hi-priority wait 0.0012s | lo-priority wait 0.0094s
```

## Notes

- Makespan barely moves (0.0182 vs 0.0187s): the scheduler does not do more
  work, it decides whose work happens first.
- Priority scheduling cuts high-priority wait 6x (0.0074 -> 0.0012s) while
  low-priority wait grows (0.0074 -> 0.0094s) — the wait distribution is
  the entire difference between the two policies.
