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

## How you find it: the slate metric-agreement audit, executed

The failure mode this stage prices is metric disagreement: the
item-level metric and the slate-level metric rank the same page
differently, so an item-only report picks the wrong winner exactly
where the slate is near-tied. The audit
([record](runs/2026-08-07-slate-metric-agreement-audit.md)) stratifies
a 20-comparison log by head and tail and reports where the two metrics
pick different winners:

| stratum | comparisons | item-sum wins a | slate-value wins a | agree |
|---|---|---:|---:|---:|
| head | 10 | 10 | 10 | 10/10 |
| tail | 10 | 10 | 0 | 0/10 |

**Verdict:** THE METRICS AGREE ON HEAD SLATES AND FLIP ON TAIL SLATES.
On head comparisons both metrics pick the same winner; on tail
comparisons every winner flips, because the higher item-score sum loses
on slate value once diversity counts. **Decision:** report the winner
per metric and declare which metric the product optimizes before
tuning the ranker (Ie et al. 2019; Craswell et al. 2008).

## The fix and its trade

The fix is to report the winner per metric and declare which metric the
product optimizes before tuning the ranker — the item-level metric and
the slate-level metric are answers to different questions, and the
product has to say which question it is asking. The executed audit
prices the failure: head comparisons agree 10 of 10, and tail
comparisons flip every winner — the higher item-score sum loses on
slate value once diversity counts, exactly as slate_a wins 2.55 to
2.10 on item scores and loses 3.06 to 3.36 on slate value.

The trade is that slate-level optimization is harder to train than
item-level scoring: the objective must encode position, diversity, and
the interaction between items, and the declared metric constrains the
ranker to that question before tuning begins. The repair costs the
actual slate value function and measured user outcomes — an item report
that averages scores cannot see the page, and a product that declares
no metric lets each team claim the near-tied slate as its own winner
(Ie et al. 2019; Craswell et al. 2008).

## Who owns the loop

Three teams keep slate evaluation honest, and each owns a piece of
what breaks:

- **The ranking and model team** owns the objective the ranker
  optimizes. The [diverse-slate detour](when-the-slate-is-diverse/) is
  theirs: the item-score optimum and the diversity-aware optimum are
  different slates, so they have to know which one the product wants
  before tuning.
- **The evaluation and metrics team** owns the report the product
  reads. The [metric-blind-spot detour](when-the-metric-misses-diversity/)
  is theirs: an item-level metric ties slates the page metric
  separates, so their report has to see the page, not average the
  items.
- **The serving and product team** owns the placement policy the slate
  actually shows. The [position-matters detour](when-the-position-matters/)
  is theirs: clicks measure the slot, not the item, so raw click
  feedback cannot stand in for slate value, and they own the
  position de-biasing between the log and the label.

The implicit-ownership consequence: when the metric is item-level only,
no team is accountable for the page — the model team tunes item
scores, the evaluation team averages them, and the serving team ships
the placement, so the near-tied slate where the metrics flip is
claimed right by all three at once.

## Why this belongs in the mission

This is the evaluation-layer version of the mission's central claim: a
slate is not the sum of its items. The ranking models in stages 00-08
optimize item-level objectives; the user experiences a page. If the
evaluation metric reports item averages, the team tunes the wrong
thing — the metric blind-spot, diverse-slate, and position-matters
detours show the report that cannot see the page from three sides.
This stage closes that loop by making the slate the unit of
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

A third detour: [position bias makes clicks measure the slot, not the
item](when-the-position-matters/) — the executed read: the best item
by relevance (0.95) sits in slot three and gets clicked 0.285, while
the promoted item (0.90) in slot one gets clicked 0.900, so clicks
rank y above x and measure the placement, not the quality.
