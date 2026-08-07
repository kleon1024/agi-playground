# Run — learning to rank, pointwise versus pairwise, on the stage's data

**Date:** 2026-08-06
**Command:** `uv run python core/learning_to_rank.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Search ranking re-orders the retrieval candidate set. This run executes
both classic formulations — pointwise regression and pairwise ranking —
on the same eight-item labeled set and compares them by NDCG.

## Output

```
pointwise  NDCG 0.6209  order [0, 7, 1, 2, 3, 4, 6, 5]
pairwise   NDCG 0.5804  order [0, 7, 1, 4, 3, 2, 6, 5]
```

## Notes

- Both learn a linear score, but pairwise optimizes the comparison search
  cares about — "is A before B" — while pointwise optimizes absolute score.
- On small data they often agree; the NDCG gap is where the formulations
  diverge, which is why the metric, not the loss, is the arbiter.
