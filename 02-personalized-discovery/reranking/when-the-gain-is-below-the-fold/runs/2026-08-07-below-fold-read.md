# Run — the gain below the fold

**Date:** 2026-08-07
**Command:** `uv run python core/below_fold_gain.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Show the served-k divergence: a reranker whose fixes land below the
three-slot page — offline NDCG@10 improves, served NDCG@3 degrades.

## Output

```
below-the-fold gain, read (grade lists, 10 positions):
  first stage: [3, 3, 2, 1, 1, 1, 1, 2, 2, 2]
  reranker:    [3, 2, 3, 2, 2, 2, 1, 1, 1, 1]
  first  NDCG@10 0.9592  NDCG@3 1.0000
  rerank NDCG@10 0.9758  NDCG@3 0.9677

reading: the reranker promoted a grade-2 buried at position
10 up to position 4 and fixed the middle of the list — NDCG@10
improves. To do that it mis-swapped positions 2 and 3, so the
three-slot page shows a worse top-3 while the offline report
says the reranker helps. The eval k and the served k disagree;
report at the served k, audit per position, and never ship a
reranker on the strength of gains below the fold.
```

## Notes

- The same reorder improves NDCG@10 (0.9592 to 0.9758) and degrades
  NDCG@3 (1.0000 to 0.9677): the promoted grade-2 at position 4 is a
  counted gain, the mis-swap at positions 2-3 is a served loss.
- Nogueira and Cho, "Passage Re-ranking with BERT", arXiv:1901.04085,
  2019, is the cross-encoder reranker production systems deploy; its
  cost forces a shortlist, and the served page is shorter still —
  which is why the eval must report at the served k.
- The stage's served-k audit run measures the same divergence at scale:
  tail queries improve +0.080 at @10 while collapsing -0.080 at @3.
