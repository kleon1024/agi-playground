---
status: verified
level: applied
base: scratch
label: When diversity hurts
verified: 2026-08-07
---

# The diverse slate that underperforms

**Question:** [stage 06's slate assembly](../) mixes relevance with a
diversity term. This chapter reads the executed constraint run and asks
what diversity actually costs.

**Before this:** [stage 06 — mixing](../) and its executed beam search.

## The trade, executed

The run ([record](runs/2026-08-07-diversity-read.md)) builds a four-item
slate with and without a four-category requirement:

| policy | relevance | categories |
|---|---|---:|
| relevance-only | 3.20 | 3 |
| forced 4 categories | 2.70 | 4 |
| cost of the constraint | 0.50 | — |

## Two readings

**Diversity is bought with relevance.** The two strongest items share a
category (0.95 and 0.90), so the relevance-only slate takes both and
reaches only three categories. Forcing a fourth replaces the 0.90 item
with the best item of a missing category (0.40) — a measured 0.50 of
relevance for one more category. The constraint is not free, and the run
prices it exactly.

**The mixing stage decides how much diversity the user wants.** A
relevance-only slate is the right answer to "give me the best results"
and the wrong answer to "show me a range". The executed trade is the
input to that choice: the beam needs a stated price per extra category,
not a free diversity bonus. Stage 06's weight is the mechanism that makes
the price explicit rather than accidental.

## Evidence boundary

The executed hand-built item set (illustrative, deterministic). It
demonstrates the trade; real diversity also covers provider, source, and
format, each with its own measured relevance cost.

## Check your mental model

Answer each before opening it.

**1. Why does the relevance-only slate stop at three categories?**

<details>
<summary>Answer</summary>

Because the top four items by relevance happen to share a category. Items
0.95 and 0.90 are both category A, and the next two are B and C — so the
slate has three categories even though it holds four items. The category
spread is an emergent property of the ranking, which is exactly why a
diversity constraint must be explicit if the product needs it.

</details>

**2. When is the 0.50 cost worth paying?**

<details>
<summary>Answer</summary>

When the product's objective includes coverage — exploration, category
discovery, or surface variety — and the user values that coverage more
than the lost relevance. The executed run shows the 0.50 as a measured
price; the decision is whether the fourth category earns it back in
engagement or retention that a same-category second item would not
produce. Without a metric for that, the constraint is decoration.

</details>

## Next

Back to [stage 06](../), or to
[the beam that is wide enough](../when-the-beam-is-wide-enough/) for the
search-side boundary of the same assembly.
