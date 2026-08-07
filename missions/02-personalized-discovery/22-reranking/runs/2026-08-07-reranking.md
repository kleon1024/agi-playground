# Run — reranking, executed on the top-k reorder model

**Date:** 2026-08-07
**Command:** `uv run python core/rerank_top_k.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 22 asks what a second ranker adds after the first stage has cut
the candidate set. This run reorders a five-document list with a
reranker and reads how many positions change.

## Output

```
reranking top k, read:
  first stage:  ['d1', 'd2', 'd3', 'd4', 'd5']
  reranker:     ['d4', 'd2', 'd5', 'd1', 'd3']
  positions changed: 4/5

reading: the reranker reorders using features the first stage
cannot afford — d4 jumps from 4th to 1st. The first stage
recalls, the reranker refines; the division is a latency budget
split, not a preference.
```

## Notes

- Four of five positions change, so the reranker is not decoration —
  it moves the final order using features the first stage cannot afford.
- The division is a latency split: the first stage is cheap enough for
  the full candidate set, the reranker is expensive enough to see only
  the top-k, which is the constraint stage 22's detours examine.
