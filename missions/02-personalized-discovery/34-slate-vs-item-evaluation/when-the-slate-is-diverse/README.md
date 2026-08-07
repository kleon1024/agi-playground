---
status: verified
level: applied
base: scratch
label: When the slate is diverse
verified: 2026-08-07
---

# The diverse slate trades a top item for coverage

**Question:** [stage 34's slate evaluation](../) measures the page, not
the items. This chapter reads the executed selection comparison and
asks what diversity costs and buys.

**Before this:** [stage 34 — slate versus item evaluation](../) and its
executed slate-value model.

## The selection, executed

The run ([record](runs/2026-08-07-slate-is-diverse-read.md)) builds a
three-item slate two ways:

| method | slate | categories |
|---|---|---|
| item-score top-3 | i1, i2, i3 | A, A, A |
| diversity-aware | i1, i2, i4 | A, A, B |

## The reading

The item-score slate is three category-A items; the diversity-aware
slate drops one for coverage. Both are "best" under different
objectives — the item-score slate maximizes average item quality, the
diversity-aware slate maximizes page coverage. The trade is real: the
diverse slate shows one lower-scoring item so the page is not three
versions of the same thing. The evaluation metric has to say which
objective the product wants before the ranker is tuned, because the
two slates are answers to different questions.

## Evidence boundary

The executed selection over one declared item set (illustrative,
deterministic, assumed scores and categories). It demonstrates the
trade; real slate optimization needs the actual diversity objective and
measured user outcomes, which stage 34's evidence boundary states.

## Check your mental model

Answer each before opening it.

**1. When does dropping the third-best item improve the page?**

<details>
<summary>Answer</summary>

When the third-best item is redundant. i1, i2, i3 are all category A —
the user sees three similar options. Replacing i3 with i4 (category B)
trades one item's score for page-level coverage: the user sees a second
category they would otherwise miss. The improvement is not in the item
scores; it is in the page the slate composes, which is the slate-value
property stage 34 measures.

</details>

**2. Why does the metric choice come before ranker tuning?**

<details>
<summary>Answer</summary>

Because the ranker is tuned against the metric, and the two metrics
pick different winners. Tuning against item-score sum rewards
same-category top items; tuning against slate value rewards coverage.
The product has to decide what a good page is first — the metric
encodes that decision, and the ranker follows it. Tuning before the
objective is declared trains the model for the wrong page.

</details>

## Next

Back to [stage 34](../). The
[metric-blind-spot detour](../when-the-metric-misses-diversity/) shows
the reporting failure when the metric never sees diversity at all.
