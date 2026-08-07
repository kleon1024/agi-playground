# Run — the synonym that lexical retrieval cannot see, executed on the index

**Date:** 2026-08-06
**Command:** `uv run python core/synonym_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

BM25 scores exact terms, so a document about 'running footwear' is
invisible to the query 'running shoes'. This run adds the synonym document
and shows the partial-match gap.

## Output

```
query: 'running shoes'
  doc3   2.8608  running shoes lightweight breathable
  doc6   1.0448  running footwear lightweight athletic sneakers
  (doc1, doc2, doc4, doc5: 0.0000)
```

## Notes

- doc6 is semantically on-topic ('running footwear' == running shoes) but
  only partially matches — 'running' hits, 'footwear' does not equal
  'shoes' — so it is under-ranked (1.04 vs doc3's 2.86).
- Dense retrieval matches meaning, which is the gap hybrid search closes
  by running both and fusing.
