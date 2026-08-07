# Run — when the embedding is stale, executed on the indexing-coverage model

**Date:** 2026-08-07
**Command:** `uv run python core/stale_embedding.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 20 retrieves by embedding. This run reads what happens to the
catalog between embedding runs: items without a vector are unreachable.

## Output

```
stale embeddings, read:
  item_d: embedded? False -> unreachable
  item_e: embedded? False -> unreachable
  catalog: 5 items, 3 with vectors

reading: retrieval can only return what has a vector. New items
wait for the next embedding run, and their wait is a recall loss
for every query they would have answered. Embedding freshness is
an indexing pipeline decision, not a model detail.
```

## Notes

- Two of five catalog items have no vector and are unreachable by
  dense retrieval, whatever their relevance.
- Freshness is an indexing pipeline decision: the gap between embedding
  runs is a recall loss for every query the missing items would have
  answered.
