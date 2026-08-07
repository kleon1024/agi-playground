# Run — when the zero-result rate matters, executed on the abandonment model

**Date:** 2026-08-07
**Command:** `uv run python core/zero_matters.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 24 measures search. This run prices the zero-result rate through
abandonment on a daily query volume.

## Output

```
zero-result cost, read:
  daily queries: 100,000
  zero-result:   8,000 (8%)
  likely lost:   4,800 users (abandonment 60%)

reading: 8% of queries return nothing and 60% of those users
leave. The zero-result rate is not a log curiosity — it is a
coverage metric with a revenue shape, which is why it belongs
in the search report next to NDCG and MRR.
```

## Notes

- 8% of 100,000 daily queries return nothing, and 60% of those users
  abandon — an estimated 4,800 lost users a day.
- The zero-result rate is a coverage metric with a revenue shape, which
  is why it belongs in the search report next to NDCG and MRR.
