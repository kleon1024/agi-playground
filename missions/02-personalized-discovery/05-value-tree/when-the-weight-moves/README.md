---
status: verified
level: applied
base: none
label: When the weight moves
verified: 2026-08-06
---

# The weight IS the strategy

**Question:** [stage 05](../) turns several predictions into one scalar, and
its docstring makes three claims: weights reorder the slate, additive and
multiplicative combination encode different beliefs, and a click-shaped
item collapses under a product. This chapter runs those claims on the
stage's own item set.

**Before this:** [stage 05's value tree](../), including its recorded weight
sweep and auction.

## The sweep, measured

The run ([record](runs/2026-08-06-combination-sweep.md)) sweeps the
satisfaction weight 0 to 1 under both combination functions on the same 12
items:

| w_sat | additive top-1 | multiplicative top-1 |
|---:|---|---|
| 0.00 | item_8 | item_8 |
| 0.33 | item_8 | item_11 |
| 0.67 | item_5 | item_6 |
| 1.00 | item_1 | item_1 |

<!-- interactive: ValueTreeStrategy -->

## Three readings

**Weights reorder the slate.** The top-1 changes with the weight in both
functions — a platform weighting click at 0.9 optimizes for a different
outcome than one weighting satisfaction at 0.9, on the same predictions.
That is not a tuning artifact; it is the product decision expressed as
arithmetic.

**The combination function is itself a strategy choice.** The two functions
disagree at w_sat=0.33 and 0.67: same predictions, same weights, different
winners. A weighted sum treats objectives as substitutes — a very high
click can compensate a low satisfaction. A weighted product treats them as
requirements — anything near zero collapses. The click-shaped item ranks
8/12 under the sum and 11/12 under the product at w_sat=0.5, which is the
docstring's claim measured: a clickbait item does not merely lose ground
under a product, it collapses.

**When the weight is extreme, the function stops mattering.** Both converge
on item_1 at w_sat=1.0 — when satisfaction is everything, substitutes and
requirements rank identically. The disagreement lives in the middle of the
weight range, which is exactly where product strategy is decided.

## Evidence boundary

One synthetic 12-item set, one seed, two combination functions. It shows the
reordering and the function disagreement on this set; it does not claim the
specific winners generalize, and it does not re-derive the calibration
precondition (the stage's own demo covers that).

## Check your mental model

Answer each before opening it.

**1. Why do the two combination functions pick different winners at w_sat=0.5
when the weights are identical?**

<details>
<summary>Answer</summary>

Because they encode different beliefs about whether a weak dimension can be
compensated. The sum averages, so a high click rescues a low satisfaction;
the product multiplies, so a near-zero satisfaction drags the whole score
toward zero. The click-shaped item wins ground under the sum and collapses
under the product — the functions are not two implementations of the same
strategy, they are two strategies.

</details>

**2. Both functions pick item_1 at w_sat=1.0. What does that convergence
reveal about where the strategy choice lives?**

<details>
<summary>Answer</summary>

That the choice between substitutes and requirements only matters in the
middle of the weight range. When one dimension has all the weight, every
reasonable combination ranks the same way; the disagreement is confined to
the region where the platform is actually trading one objective against
another — which is exactly the region a product strategy has to decide.

</details>

## Next

Back to [stage 05's value tree](../), or forward to
[stage 06's mixing](../../06-mixing/) where the scalar this stage produces
gets assembled into a slate.
