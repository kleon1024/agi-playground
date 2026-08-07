# Run — query expansion, executed on the correction model

**Date:** 2026-08-07
**Command:** `uv run python core/edit_distance.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.10s.
**Cost:** \$0 (local lane).

## Purpose

Stage 19 asks whether query correction is retrieval pre-processing. This
run measures the edit distance from a misspelled query to candidate
catalog terms and reads what the corrected query recovers.

## Output

```
query correction, read:
  heaphones -> headphones: distance 1
  heaphones -> headsets: distance 5
  heaphones -> shoes: distance 5
  heaphones -> shorts: distance 6
  heaphones -> flights: distance 7

  corrected query: headphones

reading: BM25 on the raw query matches nothing in the index;
the corrected query matches the catalog. Correction is retrieval
pre-processing — its value is measured by the recall it recovers.
```

## Notes

- The raw query retrieves nothing; the corrected one recovers the
  catalog match, so correction is measured by recall, not by edit
  distance alone.
- The distance table is why the correction is a decision: when the
  nearest term is one edit away, the correction is cheap; when several
  candidates are near, the correction needs a context signal.
