# Run — the lexical recall audit over the emitted BM25 rankings

**Date:** 2026-08-07
**Command:** `uv run python core/bm25_retrieval.py --emit-log /tmp/bm25-envelope.json` then `uv run python prod/bm25_audit.py /tmp/bm25-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib and pandas 3.0.5.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Measure recall@3 against declared relevance per query, and find the
relevant documents the lexical index cuts: those that share no query
term and score 0.0000, so no ranker downstream can recover them.

## Output

```
lexical recall audit over the emitted rankings:
  query                  freq   recall@3  mean overlap  zero-score misses
  wireless headphones    head   1.00      2.00          -
  running shoes          head   1.00      1.50          -
  iphone camera          head   1.00      2.00          -
  laptop battery         head   1.00      2.00          -
  cheap headphones       tail   0.50      1.00          d6

  aggregate recall@3 across 5 queries: 0.90

verdict: LEXICAL GAP -- 1 of 5 queries
lost a relevant document that scored 0.0000 (cheap headphones).
The misses are tail queries, and the aggregate recall
of 0.90 hides them. A document that shares no
query term never enters the candidate set, so the ranker
downstream cannot recover it. The fix is synonym-aware
query expansion, a dense path, or hybrid fusion that
carries both candidate sources (stages 19-21).
```

## Notes

- "cheap headphones" declares d9 and d6 relevant; d6 ("affordable
  bluetooth earbuds budget friendly") shares no term with the query and
  scores 0.0000. The head queries all reach recall@3 of 1.00 — the
  aggregate of 0.90 hides the one tail miss, which is the audit's point.
- "running shoes" shows the partial-match half: d7 ("sneakers athletic
  footwear lightweight running") shares only "running", still enters the
  top-3, and recall stays 1.00. The cut is reserved for zero overlap,
  which is exactly the case expansion or a dense path must carry.
- Robertson and Zaragoza, "The Probabilistic Relevance Framework: BM25
  and Beyond", Foundations and Trends in Information Retrieval 3(4),
  2009 formalize the lexical scoring; Karpukhin et al., "Dense Passage
  Retrieval for Open-Domain Question Answering", EMNLP 2020, motivate
  the dense path the audit points to as the fix.
