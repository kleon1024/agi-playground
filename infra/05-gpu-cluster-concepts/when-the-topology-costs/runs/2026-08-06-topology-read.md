# Run — the coordination tax, read from the recorded all-reduce timings

**Date:** 2026-08-06
**Command:** `uv run python core/topology_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the timings were the chapter's recorded
2026-08-01 run).

## Purpose

The GPU-cluster chapter timed all-reduce over 200 iterations at world sizes
2, 4, 8 with a fixed 4 MB tensor. This run reads the record and lays out
the pattern.

## Output

```
all-reduce over 200 iterations, 4 MB tensor (recorded), read:
  world  2: 1.82 ms/call  (tensor 4.0 MB, fixed)
  world  4: 3.60 ms/call  (tensor 4.0 MB, fixed)
  world  8: 8.31 ms/call  (tensor 4.0 MB, fixed)
  growth vs world 2: x1.98 (world 4), x4.57 (world 8)
```

## Notes

- The tensor never changes (4 MB in every cell), so the growth is
  coordination overhead — more ranks to synchronize, more hops.
- The near-doubling per world-size doubling (x1.98, x4.57) is why the
  cluster's wiring decides the parallelism strategy: topology cost scales
  with the graph, not with the data.
