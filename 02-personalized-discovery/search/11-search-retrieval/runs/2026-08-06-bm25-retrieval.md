# Run — BM25 retrieval, executed on the stage's from-scratch index

**Date:** 2026-08-06
**Command:** `uv run python core/bm25_retrieval.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Search retrieval is a cheap first stage that returns a candidate set. This
run executes the from-scratch BM25 index over a five-document corpus and
measures the classic failure: vocabulary mismatch.

## Output

```
query: 'wireless headphones'
  doc1   1.9592  wireless headphones noise cancelling bluetooth
  doc5   0.5485  headphones price comparison review 2026
  doc2   0.5041  over ear headphones comfortable long battery
  doc3   0.0000  running shoes lightweight breathable
  doc4   0.0000  iphone pro max camera battery life

query: 'running shoes'
  doc3   3.0939  running shoes lightweight breathable
  (all others 0.0000)

query: 'iphone camera'
  doc4   2.5931  iphone pro max camera battery life
  (all others 0.0000)
```

## Notes

- BM25 scores by term frequency with length normalization (k1=1.5, b=0.75).
- The vocabulary-mismatch failure is visible: a query word absent from a
  document contributes zero, so lexical retrieval misses synonyms — the
  gap dense retrieval exists to close.
