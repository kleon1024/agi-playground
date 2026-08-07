# Run — when the tail misses, executed on the cache-stratification read

**Date:** 2026-08-07
**Command:** `uv run python core/tail_misses.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 50's detour: the cache changes the cost arithmetic, but only for
the queries that repeat. This run splits traffic into head, mid, and
tail query-frequency segments and prices each at the cache-hit cost or
the full cascade cost.

## Output

```
tail misses, read (cascade 4.0 units; cache hit 0.05 units):
  segment  traffic  hit rate  cost/query
  head        40%       95%        0.25
  mid         30%       50%        2.02
  tail        30%        0%        4.00
  blended     100%       53%        1.91

  without cache: 4.00 units/query; with cache: 1.91 units/query.

reading: the cache discounts the head and leaves the tail
paying the full 4.0 - unique queries never repeat, so they
never hit. The blended number (1.91) hides that 30% of
traffic still pays the full cascade. The tail is also where
recall dominates at scale (the stage's audit): cold queries
are exactly the recall-miss queries. A cache is a head
discount, not a capacity plan - when personalization makes
more of the traffic unique, the savings shrink with it.
```

## Notes

- The blended 1.91 units hides the tail: 30% of traffic still pays the
  full 4.0 cascade cost because unique queries never repeat and never
  hit the cache. The cache's savings are bounded by the share of
  traffic that repeats.
- The tail queries are the recall-miss queries from the stage's scale
  audit, so the two findings read together: the cache cannot help the
  tail, and the tail is where the per-query cost is highest.
