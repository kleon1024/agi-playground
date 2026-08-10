# Run — the metric that is gamed, read

**Date:** 2026-08-07
**Command:** `uv run python core/metric_game_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Engineer two rankings that exploit a stage-13 metric's blind spot and
measure what the other metric says about them: MRR is binary (any
relevant hit at position 1 scores 1.0), and NDCG is top-weighted (a
sorted top with an empty tail normalizes to 1.0).

## Output

```
metric game, read (NDCG@5 and MRR per engineered ranking):
  honest spread NDCG 0.8140  MRR 1.0000  rel [1, 2, 2, 1, 0]
  mrr gamer    NDCG 0.7519  MRR 1.0000  rel [1, 3, 3, 3, 3]
  ndcg gamer   NDCG 1.0000  MRR 1.0000  rel [3, 2, 2, 0, 0]
  both gamed   NDCG 1.0000  MRR 1.0000  rel [3, 0, 0, 0, 0]

reading:
  mrr gamer: MRR 1.0000 — identical to the honest spread — while
  NDCG drops 0.8140 to 0.7519. MRR is binary: the grade-1 hit at
  position 1 is worth the same as a grade-3 hit.
  ndcg gamer: NDCG 1.0000 — the sorted top-3 is the ideal of its
  own list — while positions 4-5 are empty. The discount makes
  the tail nearly invisible.
  both gamed: perfect on both metrics with a single relevant
  document; nothing after position 1 exists.
  The fix is the suite plus per-position NDCG@k curves: report
  several metrics and the rank-gap audit, because the metric
  being optimized is the one that gets gamed.
```

## Notes

- The mrr gamer places a grade-1 hit at position 1 and scores MRR 1.0000
  — identical to the honest spread's 1.0000 — while NDCG falls 0.8140
  to 0.7519. MRR cannot see grades or coverage past the first hit.
- The ndcg gamer scores NDCG 1.0000 because any sorted list is the ideal
  of its own grades; positions 4-5 are empty yet invisible to the
  top-weighted discount. The same lesson holds online: click-based
  metrics inherit position bias (Joachims, KDD 2002), so the games
  compound when the metric is optimized directly.
