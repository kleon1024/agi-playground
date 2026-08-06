# Run — the network tail, read from the recorded ping timing

**Date:** 2026-08-06
**Command:** `uv run python core/network_tail_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the committed JSON).
**Cost:** \$0 (local lane; the pings were the stage's recorded 2026-08-01
run).

## Purpose

Stage 03's realtime margin is dominated by the network, not the codec.
This run reads the recorded ping distribution and lays out the round-trip
tail.

## Output

```
  p50 9.7ms  p95 42.5ms  mean 15.1ms  min 6.1ms  max 85.3ms
  p95/p50 ratio: 4.4x
  200 pings, 64 bytes each way
```

## Notes

- A 48-token completion decodes in ~72ms on this lane; the network p50
  adds ~10ms, but the p95 (42ms) and max (85ms) round trips are a
  significant fraction of the budget.
- The tail is where the realtime contract lives — p95 is 4.4x p50.
