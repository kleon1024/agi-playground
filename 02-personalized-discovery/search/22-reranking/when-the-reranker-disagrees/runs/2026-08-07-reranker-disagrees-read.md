# Run — when the reranker disagrees, executed on the two-ranker model

**Date:** 2026-08-07
**Command:** `uv run python core/reranker_disagrees.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 22 adds a reranker after the first stage. This run compares the
two orders and reads whether the top-3 agrees.

## Output

```
reranker disagreement, read:
  first stage: ['d1', 'd2', 'd4', 'd3', 'd5']
  reranker:    ['d3', 'd2', 'd5', 'd4', 'd1']
  same top-3:  False

reading: the first stage ranks by cheap signals, the reranker
by rich ones, and they disagree on d2/d3. The disagreement is
the point — if they always agreed, the reranker would be dead
weight. It is also the risk: the budget only reranks a pool,
and anything outside it keeps the first stage's verdict.
```

## Notes

- The first stage and the reranker disagree on the top-3 — the
  disagreement is the reranker's reason to exist.
- It is also the risk: anything outside the reranked pool keeps the
  first stage's cheaper verdict, so the pool boundary is a quality
  decision.
