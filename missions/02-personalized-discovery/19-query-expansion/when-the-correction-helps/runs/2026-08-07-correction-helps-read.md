# Run — when the correction helps, executed on the recall-recovery model

**Date:** 2026-08-07
**Command:** `uv run python core/correction_helps.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 19 corrects the query. This run measures the correction's value
as the recall it recovers: hits on the raw query versus the corrected
one.

## Output

```
correction helps, read:
  raw query 'heaphones': 0 document hits
  corrected 'headphones': 3 document hits

reading: the raw query retrieves nothing, the corrected one
finds three documents. The correction's value is the recall it
recovers — a retrieval-side metric, not a query-side nicety.
```

## Notes

- Raw query retrieves zero documents; corrected query retrieves three.
- The value is measured at retrieval, not at the query string, which is
  why correction belongs before the index, not after it.
