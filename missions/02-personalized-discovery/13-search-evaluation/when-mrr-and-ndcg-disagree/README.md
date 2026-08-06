---
status: verified
level: applied
base: scratch
label: When MRR and NDCG disagree
verified: 2026-08-06
---

# The metric chooses the winner

**Question:** [stage 13's evaluation](../) computes NDCG and MRR. This
chapter reads the executed rankings and shows the metric's blind spot —
the case where MRR cannot separate quality.

**Before this:** [stage 13 — search evaluation](../) and its executed
metrics.

## The blind spot, executed

The run ([record](runs/2026-08-06-metric-disagree.md)) computes both
metrics on three rankings:

| ranking | NDCG | MRR |
|---|---:|---:|
| one perfect hit, rest empty | 1.000 | 1.000 |
| strong hits, mis-ordered | 0.871 | 1.000 |
| mediocre hits, mis-ordered | 0.922 | 1.000 |

## Two readings

**MRR records only the first relevant hit's position.** All three rankings
have their first hit at position 1, so all three score MRR 1.0 — MRR
cannot tell "one good hit and nothing else" from "strong results buried
below." The executed rows make the blind spot concrete: identical MRR,
different NDCG.

**NDCG separates them by how the material below is graded and placed.**
The perfect-hit ranking scores 1.000; the mis-ordered strong hits score
0.871 (the 3 at position 1 is ideal, but the 2s at positions 3 and 5 are
discounted); the mediocre mis-order scores 0.922. The graded, top-weighted
metric sees what MRR cannot — which is why evaluation reports both, and
why the metric choice is declared before the system is built.

## Evidence boundary

The executed metrics over three hand-built graded rankings (illustrative,
deterministic). It demonstrates the metric properties; real search
evaluation needs relevance labels from humans or corrected clicks.

## Check your mental model

Answer each before opening it.

**1. Why is MRR 1.0 for all three when the quality differs?**

<details>
<summary>Answer</summary>

Because MRR is defined by the first relevant position only — all three
have a relevant item at position 1, so all three score 1/1. Everything
after the first hit is invisible to MRR by construction. The metric does
not fail; it measures exactly what it claims, and what it claims is
insufficient for grading quality below the first hit.

</details>

**2. Why does the mis-ordered strong ranking score lower NDCG than the
mediocre one?**

<details>
<summary>Answer</summary>

Because NDCG normalizes against each ranking's own ideal permutation.
The strong ranking's ideal (3, 2, 2 at top) is harder to achieve than the
mediocre one's ideal (3, 1, 1), so the same placement quality leaves the
strong ranking further from its ceiling (0.871) than the mediocre one from
its own (0.922). The cross-ranking comparison is about relative placement,
which is exactly what a ranking metric should measure.

</details>

## Next

Back to [stage 13](../), or forward to
[stage 14 — ad auction](../../14-ad-auction/) where a paid item competes for
the same slot.
