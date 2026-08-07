# Run — when the rerank budget is tight, executed on the cutoff model

**Date:** 2026-08-07
**Command:** `uv run python core/tight_rerank.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 22 reranks the first stage's top-k. This run varies k and reads
which documents the reranker can never see.

## Output

```
  k=3: reranker sees top 3, d5 reachable: False
  k=4: reranker sees top 4, d5 reachable: False
  k=5: reranker sees top 5, d5 reachable: True

reading: with k=3 or 4, d5 never reaches the reranker and its
0.99 score is never seen. The first stage's cutoff is a filter
on what the reranker can fix — a tight budget hides recall.
```

## Notes

- A document with a 0.99 reranker score is unreachable at k=3 or k=4;
  only k=5 lets the reranker see it.
- The first stage's cutoff filters what the reranker can fix, so a
  tight rerank budget hides recall that the expensive model would have
  recovered.
