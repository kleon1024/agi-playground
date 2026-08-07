# Run — when the embedding expires, executed on the stale-index read

**Date:** 2026-08-07
**Command:** `uv run python core/embedding_expires.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 46's detour: item embeddings are computed once at ingestion. This
run compares recall under stale and refreshed embeddings against the
current query.

## Output

```
embedding expires, read (similarity to the query):
  item   stale embedding  refreshed embedding
  P1001   0.81             0.30
  P1002   0.55             0.85
  P1003   0.42             0.78
  P1004   0.38             0.22
  P1005   0.25             0.60
  recall@3 with stale embeddings:     2/3
  recall@3 with refreshed embeddings: 3/3

reading: the stale vectors were computed for the taste of the
day they were ingested; the refreshed ones match the current
query. Recall recovers 2/3 to 3/3 - the embedding
is a dated snapshot, and 'retrain' must reach the index,
not just the model weights.
```

## Notes

- Stale embeddings give recall@3 of 2/3; refreshed embeddings give 3/3.
- The embedding is a dated snapshot, and retrain must reach the index, not just the model weights.
