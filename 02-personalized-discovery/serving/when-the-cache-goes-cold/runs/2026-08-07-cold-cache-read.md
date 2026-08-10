# Run — the cache that misses together, executed on the refresh policy

**Date:** 2026-08-07
**Command:** `uv run python core/cold_cache_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 08's serving path keeps a p95 budget. This run compares a
synchronized cache refresh (stampede) against a staggered one.

## Output

```
  synchronized refresh: p95 50 ms
  staggered refresh:    p95 2 ms
```

## Notes

- Cache misses are cheap alone and expensive together.
- A synchronized refresh converts a cold window into a p95 breach;
  staggering the same refreshes keeps the tail flat. Tail latency is a
  scheduling property as much as a compute one.
