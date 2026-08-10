# Run — when the cache pays, executed on the hit-rate sweep

**Date:** 2026-08-07
**Command:** `uv run python core/cache_pays.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 50's detour: a hot item's slate is computed once and served many
times. This run computes the per-served-query cost across hit rates.

## Output

```
cache pays, read (cost units per served query, full cost 4.0):
  hit rate 0%: 4.00 units per served query
  hit rate 50%: 2.02 units per served query
  hit rate 90%: 0.44 units per served query
  hit rate 99%: 0.09 units per served query

reading: at 90% hits the per-served cost drops to a tenth
of the full path. The cache is not free - it trades freshness
for cost, and a stale cached slate is the same trade as a
stale model. The hit-rate curve is where the cache decision
is measured.
```

## Notes

- At 90% hits the per-served cost is 0.44 units, a tenth of the full path's 4.0.
- The cache trades freshness for cost; a stale cached slate is the same trade as a stale model.
