---
status: verified
level: applied
base: scratch
label: When the label is a click
verified: 2026-08-06
---

# The label that carries the position's bias

**Question:** [stage 12's search ranking](../) trains on relevance labels,
but production rarely has human grades — it has clicks. This chapter reads
the exposure-bias model and asks why clicks are not relevance.

**Before this:** [stage 12 — search ranking](../) and [stage 13's
evaluation](../../13-search-evaluation/) for what the labels feed into.

## The bias, executed

The run ([record](runs/2026-08-06-click-label-read.md)) executes the
exposure model (observed = relevance x exposure):

| position | observed | relevance | exposure |
|---:|---:|---:|---:|
| 1 | 0.80 | 0.8 | 1.0 |
| 2 | 0.30 | 0.6 | 0.5 |
| 3 | 0.10 | 0.4 | 0.25 |

## Two readings

**A click is relevance times exposure, and exposure is positional.** The
same item clicked more at position 1 than position 3 is exposure, not
relevance — users simply see the top first. A ranker trained on raw
clicks learns to exploit this: putting anything at the top increases its
clicked label, so the model optimizes position rather than meaning.

**Making clicks usable means removing the bias.** Inverse-propensity
weighting divides each click by its position's exposure, recovering an
unbiased estimate of relevance. The lesson is that implicit labels are
not free grades — they carry the recording process's bias, and the
correction is part of the labeling, not a downstream afterthought.

## Evidence boundary

The executed bias model over one hand-built relevance set (illustrative,
deterministic). It demonstrates the mechanism; real IPW needs measured
exposure from the serving logs.

## Check your mental model

Answer each before opening it.

**1. Why does the position-1 item look best when it is not?**

<details>
<summary>Answer</summary>

Because exposure multiplies relevance. Item A's 0.8 relevance at position
1 gets full exposure (1.0) so its observed click rate is 0.8; item B's
0.6 at position 2 gets half exposure, observed 0.30. Raw click labels
would say A is far better than B — the true gap is 0.2, the observed gap
is 0.5. Exposure inflates the top, which is the bias.

</details>

**2. What does inverse-propensity weighting actually compute?**

<details>
<summary>Answer</summary>

It divides each observed click by the probability it was seen — the
exposure — so an item at position 2's 0.30 becomes 0.30/0.5 = 0.60, its
true relevance. Each label is reweighted to undo the recording process's
distortion, which is what turns a biased click log into a usable training
signal.

</details>

## Next

Back to [stage 12](../), or to
[stage 13's metric blind spots](../../13-search-evaluation/when-mrr-and-ndcg-disagree/)
for how the resulting ranker is judged.
