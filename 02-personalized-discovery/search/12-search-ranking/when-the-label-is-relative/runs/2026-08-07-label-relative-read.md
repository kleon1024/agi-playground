# Run — the label that is relative, read

**Date:** 2026-08-07
**Command:** `uv run python core/label_relative_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Sweep single-grade perturbations of the stage's labeled set, re-fit the
pairwise ranker, and measure which grader disagreements actually move
the learned order — the concentration the label-consistency audit
identifies as the case-finding.

## Output

```
label is relative, read (single boundary flips of one item):
  baseline: NDCG 0.5804  order [0, 7, 1, 4, 3, 2, 6, 5]
  item 0 grade 1 -> 0: NDCG 0.5804, pref flips 0
  item 0 grade 1 -> 2: NDCG 0.5804, pref flips 0
  item 1 grade 2 -> 1: NDCG 0.5804, pref flips 0
  item 1 grade 2 -> 3: NDCG 0.5804, pref flips 0
  item 2 grade 3 -> 2: NDCG 0.5804, pref flips 0
  item 3 grade 2 -> 1: NDCG 0.5804, pref flips 0
  item 3 grade 2 -> 3: NDCG 0.5804, pref flips 0
  item 4 grade 0 -> 1: NDCG 0.5804, pref flips 0
  item 5 grade 3 -> 2: NDCG 0.5804, pref flips 0
  item 6 grade 1 -> 0: NDCG 0.5804, pref flips 0
  item 6 grade 1 -> 2: NDCG 0.5727, pref flips 1  <-- visible
  item 7 grade 1 -> 0: NDCG 0.5804, pref flips 0
  item 7 grade 1 -> 2: NDCG 0.5804, pref flips 0

  1 of 13 single flips moved the learned order;
  the visible one is item 6, the item on the smallest-margin
  boundary of the learned score. Two-flip re-gradings swing
  NDCG more: batch B moves it to 0.5727, batch C to 0.6209.

reading: most grader disagreements are invisible to the ranker;
the ones that bite are concentrated on the learned decision
boundary. That concentration is why redundant grading (majority
vote across graders) and margin-aware pairwise losses exist.
```

## Notes

- Twelve of thirteen single ±1 flips leave NDCG and the learned order
  unchanged; the exception is item 6 raised 1 to 2, whose pair with
  item 2 sits on the smallest-margin boundary of the clean fit (margin
  0.0439, third smallest of 23). Label noise is invisible until it
  crosses a learned decision boundary.
- The two-flip re-gradings from the audit (batches B and C) swing NDCG
  to 0.5727 and 0.6209 — the spread the audit reports as PAIRWISE
  INCONSISTENT. The detour shows why the direction gate undercounts:
  most of the movement is boundary concentration, not grade-order
  reversal.
