---
status: verified
level: applied
base: scratch
label: When the position matters
verified: 2026-08-07
---

# Position bias makes clicks measure the slot, not the item

**Question:** [stage 34's slate evaluation](../) measures the page, and
clicks are the cheapest feedback a served page earns. This chapter
reads why clicks lie about quality.

**Before this:** [stage 34 — slate versus item evaluation](../) and the
[metric-blind-spot detour](../when-the-metric-misses-diversity/).

## The position, executed

The run ([record](runs/2026-08-07-position-bias-read.md)) serves three
items in an order that is not relevance order and multiplies each
item's relevance by the slot's examination probability:

| slot | item | relevance | examine | click prob |
|---|---|---:|---:|---:|
| 1 | y | 0.90 | 1.00 | 0.900 |
| 2 | z | 0.80 | 0.60 | 0.480 |
| 3 | x | 0.95 | 0.30 | 0.285 |

## The reading

The best item by relevance (x, 0.95) sits in slot three and gets
clicked 0.285; the promoted item (y, 0.90) in slot one gets clicked
0.900. Clicks rank y above x, so an evaluation that reads clicks as
quality measures the slot, not the item. This is why the slate-value
metric in stage 34 has to account for where an item sits, and why
clicks must be de-biased for position (examination models,
position-weighted metrics) before they become labels or a verdict —
otherwise the model is trained and judged on the placement policy's
biases, not on relevance.

## Evidence boundary

The executed multiplication over one declared served order
(illustrative, deterministic, assumed examination probabilities). It
demonstrates the mechanism — click probability factorizes into
examination times relevance — but real position bias is estimated from
logged data (examination models fit on click logs, randomization for
inverse-propensity weighting), and the de-biasing method and its
variance are a measured decision.

## Check your mental model

Answer each before opening it.

**1. Why does the best item lose the click race?**

<details>
<summary>Answer</summary>

Because the click is gated by examination. The user sees slot one first
and drifts away; slot three gets far less examination (0.30 vs 1.00).
The best item earns a high probability of click given examination
(0.95), but the probability it is ever examined is low, so its click
probability is 0.285. Click feedback confounds relevance with
placement.

</details>

**2. What breaks if clicks are used as labels without de-biasing?**

<details>
<summary>Answer</summary>

The model learns the placement policy, not the item. y looks better
than x in the click log even though x is more relevant, so a ranker
trained on raw clicks reinforces the promoted placement instead of
correcting it, and the evaluation that reports click-based metrics
declares the policy correct. Position de-biasing — examination models,
IPS weighting — has to sit between the log and both the label and the
verdict.

</details>

## Next

Back to [stage 34](../). The
[diverse-slate detour](../when-the-slate-is-diverse/) shows the
selection side: which top item the slate metric trades for coverage.
