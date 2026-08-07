# Run — when the fan-out tails, executed on the tail-amplification read

**Date:** 2026-08-07
**Command:** `uv run python core/fanout_tails.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 49's detour: capacity planning sized one server, but a real query
fans out to many shards and is as slow as its slowest shard. This run
measures the query-level miss rate over a 500ms budget at fan-out 1, 5,
and 20, plus a hedged variant (two copies, first to finish wins) at
fan-out 20.

## Output

```
fan-out tails, read (10k queries; shards 10ms/150ms/800ms; budget 500ms):
    fan-out    p99 over 500ms
          1    800ms       1.1%
          5    800ms       5.2%
         20    800ms      18.5%
  hedged-20    800ms       3.4%

reading: the query is as slow as its slowest shard, so the
same 1% slow component becomes a 18% slow query
at fan-out 20 (from 1% at fan-out 1) while
per-shard latency never changes - the tail amplifies with the
fan-out factor. Hedging - two copies, first to finish wins -
cuts the miss rate to 3.4% at 2x the shard work.
This is the tail at scale: capacity planning for a fan-out
system must budget for the max over shards, not the mean.
```

## Notes

- The query is the max over its shards, so the same 1% slow component
  (800ms) produces a miss rate of 1.1% at fan-out 1, 5.2% at fan-out 5,
  and 18.5% at fan-out 20 — the tail amplifies with the fan-out factor
  while per-shard latency never changes (Dean and Barroso, "The Tail at
  Scale", Communications of the ACM, 2013).
- Hedging cuts the miss rate to 3.4% because a query only misses when
  both copies draw a slow shard (0.185^2); the price is 2x shard work,
  which is why hedging is a budget decision rather than a default.
