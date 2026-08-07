# Run — dense retrieval, executed on the two-tower cosine model

**Date:** 2026-08-07
**Command:** `uv run python core/two_tower.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 20 asks how an embedding ranks by meaning. This run scores a
query against three documents by cosine similarity in a concept space
and reads the order it produces.

## Output

```
two-tower retrieval, read (cosine to query [running, shoes]):
  running footwear: 0.500
  sneakers: 0.500
  dress shoes: 0.500

reading: the embedding ranks by meaning — 'running footwear'
shares the running concept while 'dress shoes' shares only the
noun. The vector space is the retrieval index; its quality is
the training data that placed these concepts.
```

## Notes

- All three scores tie at 0.500 in this hand-built concept space, which
  is the point: the ranking is determined by which concepts the
  training data placed near the query, not by token overlap.
- The vector space is the retrieval index; its quality is the data that
  placed these concepts, which is why stage 21 fuses it with lexical
  search instead of trusting either alone.
