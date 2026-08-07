---
status: verified
level: applied
base: scratch
label: When the label is relative
verified: 2026-08-07
---

# The grader's boundary judgment moves the ranker, not the model

**Question:** [stage 12's ranker](../) trains on ordinal grades, and an
ordinal grade is a judgment, not a measurement. This chapter measures
what a second grader's boundary judgment does to the learned order, and
why most of it is invisible — until it crosses the decision boundary.

**Before this:** [stage 12 — search ranking](../) for the pairwise fit,
and the stage's label-consistency [audit run](../runs/2026-08-07-search-ranking-audit.md)
that names the case-finding first.

## The sweep, executed

The run ([record](runs/2026-08-07-label-relative-read.md)) re-fits the
pairwise ranker under every single ±1 grade flip of the stage's
eight-item set:

| perturbation | NDCG | learned preferences flipped |
|---|---:|---:|
| baseline (batch A) | 0.5804 | 0 |
| 12 of 13 single ±1 flips | 0.5804 | 0 |
| item 6: grade 1 to 2 | 0.5727 | 1 |
| two-flip re-grading B | 0.5727 | 1 |
| two-flip re-grading C | 0.6209 | 3 |

## Two findings

**Most grader disagreements are invisible to the ranker.** Twelve of
thirteen single flips leave NDCG and the learned order exactly
unchanged — moving a boundary grade by one usually does not change which
item wins its pairwise comparisons. The one flip that bites is item 6,
whose pair with item 2 sits on the smallest-margin boundary of the clean
fit (margin 0.0439, third smallest of 23). Label noise is concentrated:
it moves the model only where the learned score is already undecided.

**The concentration is why the audit re-fits instead of comparing grade
orders.** Two-flip re-gradings swing NDCG to 0.5727 and 0.6209 with zero
model change, and batch C flips three learned preferences while changing
no pair direction — the direction-only gate the audit runs first
undercounts the fragility. The production fixes follow from the
mechanism: redundant grading with majority vote dilutes single-grader
boundary noise, and margin-aware or list-aware losses — Burges, "From
RankNet to LambdaRank to LambdaMART: An Overview", MSR-TR-2010-82
(2010) — smooth the objective where small label movements would
otherwise flip a preference. The ranker downstream in
[stage 13](../../13-search-evaluation/) then inherits a label set, and
its metrics inherit the same fragility, which is why the audit contract
holds the labels to the same scrutiny as the model.

## Evidence boundary

The sweep re-fits the stage's own eight-item set under declared
perturbations (illustrative, deterministic). It measures the mechanism —
boundary concentration of label sensitivity — not a real grading
process's noise rate, which needs two real graders on a production
labeling task.

## Check your mental model

Answer each before opening it.

**1. Why do 12 of 13 single flips leave the ranker unchanged?**

<details>
<summary>Answer</summary>

Because a one-grade move usually does not cross any learned decision
boundary: the item's pairwise wins and losses stay the same, so the
least-squares fit barely moves. The flip only matters where the learned
score is already near a tie — the smallest-margin pairs — where a tiny
weight change reverses a preference. Sensitivity to labels is a property
of the boundary, not of the label change itself.

</details>

**2. What does "batch C changes no pair direction yet flips three
preferences" prove?**

<details>
<summary>Answer</summary>

That grade-order agreement between graders is not the same as ranker
agreement. A direction-only consistency check compares the two gradings;
the ranker is fit on the whole loss landscape, so small grade shifts
re-weight every pair and can reverse the lowest-margin preferences even
when no individual pair's direction reversed. The audit must re-run the
fit, not diff the labels.

</details>

## Next

Back to [stage 12](../), or forward to
[stage 13 — search evaluation](../../13-search-evaluation/) where the
metric decides what "worked" means.
