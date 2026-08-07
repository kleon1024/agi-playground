# Run — search evaluation metrics, executed on four rankings

**Date:** 2026-08-06
**Command:** `uv run python core/search_eval.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Search evaluation answers "did the ranking work" with a metric, and the
metric choice changes what gets optimized. This run computes NDCG@5 and
MRR on four rankings with different failure shapes.

## Output

```
  A: one good hit early  NDCG@5 1.0000  MRR 1.0000  rel [3,0,0,0,0]
  B: good spread         NDCG@5 0.8140  MRR 1.0000  rel [1,2,2,1,0]
  C: good at top         NDCG@5 1.0000  MRR 1.0000  rel [3,2,0,0,0]
  D: reversed            NDCG@5 0.2750  MRR 0.2500  rel [0,0,0,2,3]
```

## Notes

- MRR rewards "first hit early" and ignores the rest; B's good spread and
  A's single hit score identically (MRR 1.0000).
- NDCG rewards graded relevance weighted to the top; D's reversed ranking
  scores 0.275, showing the metric's sensitivity to ordering.
