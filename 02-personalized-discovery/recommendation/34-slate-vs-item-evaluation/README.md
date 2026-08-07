---
status: verified
level: applied
base: scratch
label: Slate versus item evaluation
verified: 2026-08-07
---

# The user experiences the slate, not the item

**Question:** every evaluation so far scored items. This stage asks what
the user actually experiences — a page, not a list of independent
scores — and answers: the slate, which is why an item-level metric can
rank the wrong winner.

**Before this:** [stage 06 — mixing](../../shared/06-mixing/) for slate assembly
and diversity, and [stage 09 — report](../../shared/09-report/) for how the
mission turns metrics into verdicts.

## The comparison, executed

The run ([record](runs/2026-08-07-slate-vs-item-evaluation.md)) scores
two slates two ways:

| slate | item-score sum | slate value |
|---|---:|---:|
| a | 2.55 | 3.06 |
| b | 2.10 | 3.36 |

## The mechanism, named

Item-score sum adds the scores of the items; slate value adds their
contributions to the page, including the diversity adjustment that
stage 06 introduced. slate_a wins on item scores (2.55 vs 2.10) but
loses on slate value (3.06 vs 3.36) once diversity counts — the items
look better in isolation and compose into a worse page. The two
numbers are answers to different questions, and the product has to say
which question it is asking.

## Why this belongs in the mission

This is the evaluation-layer version of the mission's central claim: a
slate is not the sum of its items. The ranking models in stages 00-08
optimize item-level objectives; the user experiences a page. If the
evaluation metric reports item averages, the team tunes the wrong
thing — the metric blind-spot detour shows the report that cannot see
the page. This stage closes that loop by making the slate the unit of
evaluation, the way the funnel made it the unit of assembly.

## Evidence boundary

The executed comparison over two hand-built slates (illustrative,
deterministic, assumed item scores and diversity adjustment). It
demonstrates the mechanism; real evaluation needs the actual slate
value function and measured user outcomes, which an online experiment
would estimate.

## Check your mental model

Answer each before opening it.

**1. How can a slate with lower item scores be the better page?**

<details>
<summary>Answer</summary>

Because the page's value is not the sum of its items. Ten near-identical
high-scoring items compose badly — the user sees ten versions of the
same thing. slate_b's lower item scores buy diversity, and the
diversity-adjusted slate value (3.36) beats slate_a's (3.06) even
though slate_a's items average higher. The item scores rank items; the
slate value ranks pages.

</details>

**2. What does the evaluation metric have to declare before the ranker
is tuned?**

<details>
<summary>Answer</summary>

Whether it optimizes items or slates. The same two slates produce
opposite winners under the two metrics, so tuning against item-score
sum and tuning against slate value pull the ranker in different
directions. The product decision — what a good page is — has to come
first, and the metric is the mechanism that encodes it.

</details>

## Next

This closes the frontier recommendation track (stages 31-34). The
mission's search frontier begins next with [stage 35 — generative
retrieval](../../search/35-generative-retrieval/).

A detour from here: [the diverse slate trades a top item for
coverage](when-the-slate-is-diverse/) — the executed read: the
item-score top-3 is all category A, while the diversity-aware slate
drops one for coverage, and both are best under different objectives.

Another detour: [the item-level metric misses diversity and ties
the slates](when-the-metric-misses-diversity/) — the executed read: the
item-sum ties at 2.40 = 2.40 while the slate value separates 2.88 from
3.84, so a report that averages item scores cannot see the page.
