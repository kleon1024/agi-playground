# Run — the pairwise label-consistency audit over the grading batches

**Date:** 2026-08-07
**Command:** `uv run python core/learning_to_rank.py --emit-log /tmp/ltr-envelope.json` then `uv run python prod/ltr_audit.py /tmp/ltr-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib and pandas 3.0.5.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Check whether the stage-12 ranker's learned pairwise preferences are
stable across plausible re-gradings of the same items, and find the
label fragility that a direction-only consistency gate misses.

## Output

```
pairwise label-consistency audit over the grading batches:
  batch  direction disagr.  learned-pref flips  NDCG@A   NDCG@self
  A        0                0             0.5804  0.5804
  B        1                1             0.5727  0.5322
  C        0                3             0.6209  0.7164

  NDCG@A spread across re-gradings: 0.5727 - 0.6209

verdict: PAIRWISE INCONSISTENT -- two plausible grading passes
flip up to 3 of the ranker's learned pair preferences, and
offline NDCG moves with zero model change. Batch C changes no
pair direction yet flips the most preferences: a direction-only
consistency gate undercounts label fragility. The labels, not
the model, are the fragile component; redundant grading or a
margin-aware loss is the fix.
```

## Notes

- Batch B moves the two grade-0/1 boundary items (item 4: 0 to 1, item
  7: 1 to 0); batch C moves a grade-3 and a grade-1 item (item 5: 3 to
  2, item 7: 1 to 2). Both are single-grade boundary judgments, the kind
  a second grader makes without being wrong.
- The spread is the point: NDCG@A moves 0.5727-0.6209 with the model
  class, features, and training procedure unchanged. Batch C flips three
  learned preferences while changing zero pair directions, which is why
  the audit re-fits the ranker instead of only comparing grade orders.
- The flipped pairs are the smallest-margin pairs of the clean fit
  (margins 0.017-0.056, the four smallest of 23), which is the
  boundary-concentration the when-the-label-is-relative detour measures.
- Burges, "From RankNet to LambdaRank to LambdaMART: An Overview",
  MSR-TR-2010-82 (2010) is the reference for how pairwise objectives
  relate to the ranking metric and why smooth, list-aware losses are the
  production answer to label sensitivity.
