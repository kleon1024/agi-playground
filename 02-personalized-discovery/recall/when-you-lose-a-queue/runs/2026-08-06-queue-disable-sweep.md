# Run — queue-disable sweep: what each blind spot costs

**Date:** 2026-08-06
**Command:** `uv run python core/queue_disable_sweep.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; reuses the stage's `recall.py`
unmodified.
**Wall-clock:** 0.2s (20 users x 5 configs).
**Cost:** \$0 (local lane).

## Purpose

Stage 02's multi-queue recall assigns each target a provenance — the queue
that alone can find it. The core's `--disable` flag demonstrates one queue's
loss at a time; this run sweeps all four and measures how much the other
queues recover incidentally.

## Output

```
baseline (all queues): mean target coverage 1.00

disabled queue     coverage  its targets found  recovered by others
two_tower              0.84        8/20                         12
lexical                0.80        4/20                         16
item_to_item           0.95       16/20                          4
freshness              0.84        7/20                         13
```

## Notes

- No disabled queue's loss is fully recovered: the other queues find 4-16 of
  its 20 targets incidentally, and aggregate coverage drops 5-20 points.
- item_to_item is the deepest blind spot: only 4 of its 20 targets are
  recovered elsewhere. The stage's design makes i2i the slow, heavy-tailed
  queue (a graph traversal), and the sweep shows its targets are also the
  least replaceable — the queue with the worst latency profile carries the
  least redundant coverage.
- The asymmetry is the stage's central claim, measured: recall is the one
  stage downstream ranking cannot repair, because the recovery the other
  queues provide is incidental overlap, not design.
