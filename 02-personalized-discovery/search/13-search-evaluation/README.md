---
status: verified
level: applied
base: scratch
label: Search evaluation
verified: 2026-08-06
---

# What search success means, and what each metric hides

**Question:** search evaluation answers "did the ranking work" with a
metric — and the metric choice changes what gets optimized. This stage
computes NDCG@k and MRR and shows their blind spots.

**Before this:** [stage 12 — search ranking](../12-search-ranking/) for the
ranker, and [mission 01's evaluation](../../../01-language-model/07-eval/)
for why a metric must be disclosed.

## The metrics, executed

The run ([record](runs/2026-08-06-search-eval.md)) computes both metrics
on four rankings:

| ranking | NDCG@5 | MRR |
|---|---:|---:|
| A: one good hit early | 1.0000 | 1.0000 |
| B: good spread | 0.8140 | 1.0000 |
| C: good at top | 1.0000 | 1.0000 |
| D: reversed | 0.2750 | 0.2500 |

## The mechanisms, named

1. **NDCG** — graded relevance, discounted by position, normalized against
   the ideal ordering. Rewards putting relevant items high and is
   sensitive to grade.
2. **MRR** — the reciprocal rank of the first relevant hit. Rewards one
   early hit and ignores everything after it.

## The blind spots, executed

B's "good spread" (grades 1, 2, 2, 1) scores NDCG 0.814 but MRR 1.0000 —
identical to A's single good hit. MRR cannot tell "one good hit" from "a
consistently decent ranking." And C's NDCG 1.0000 hides that the third
position, grade 0, is a miss the ideal would have avoided — NDCG is
insensitive to what sits below the top-weighted region when the top is
correct. The metrics agree on the extremes (D is clearly bad) and disagree
where the decision actually is, which is why evaluation reports several
metrics together.

## Evidence boundary

The executed metrics over four hand-built graded rankings (illustrative).
It demonstrates the metric properties; real search evaluation also needs
relevance labels from humans or clicks, which this stage does not model.

## Check your mental model

Answer each before opening it.

**1. Why is MRR identical for "one good hit" and "good spread"?**

<details>
<summary>Answer</summary>

Because MRR only looks at the first relevant position. Both A and B have
their first relevant hit at position 1, so both score 1.0000 — MRR cannot
see that B keeps delivering after the first hit while A stops. That is the
metric's blind spot: it rewards a single early hit and ignores the rest
of the list.

</details>

**2. What does the D row (reversed) prove about NDCG?**

<details>
<summary>Answer</summary>

That NDCG is sensitive to ordering, not just presence. D has the same
grades as B but in reverse, and scores 0.2750 against B's 0.8140 — the
top-weighted discount punishes putting relevant items low. That ordering
sensitivity is exactly what a ranking metric must have, which is why NDCG
is the search analogue of the mission's nDCG@10 primary metric.

</details>

## Next

This closes the search track. Forward to [stage 14 — ad auction](../../ads/14-ad-auction/)
where a paid item competes for the same slot.

A detour from here: [the metric chooses the winner](when-mrr-and-ndcg-disagree/) — the executed metrics read: three rankings score MRR 1.0 while NDCG separates them, MRR's blind spot below the first hit.

Another detour: [NDCG@1 is a different claim than NDCG@5](when-the-k-is-small/) — the executed k-sweep read: the same ranking is 0.000 at @1 and 0.546 at @5, so k is part of the evaluation contract.
