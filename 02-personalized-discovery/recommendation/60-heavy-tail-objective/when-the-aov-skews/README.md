---
status: verified
level: applied
base: scratch
label: When the AOV skews
verified: 2026-08-07
---

# The rate and the amount move independently

**Question:** [stage 60](../) regresses GMV. This chapter asks whether GMV
is one thing, and answers: it is the product of an order probability and a
conditional amount that move independently, so a product change that moves
AOV should not silently re-train the order model.

**Before this:** [stage 60 — heavy-tail objective](../).

## The three cohorts, executed

The run ([record](runs/2026-08-07-aov-skews.md)) reads three cohorts with
the same expected GMV:

| cohort | p(order) | e(gmv\|order) | e(gmv) |
|---|---:|---:|---:|
| standard | 0.030 | 25.00 | 0.75 |
| premium | 0.030 | 90.00 | 2.70 |
| flash sale | 0.060 | 18.00 | 1.08 |

## The reading

Expected GMV is the product of a rate and an amount, and the two move
independently: a flash sale doubles the rate and halves the AOV for the
same expected value as standard. Regressing GMV directly mixes both
effects into one coefficient, so a pricing change that moves AOV quietly
re-fits the order model and a launch that moves the rate re-fits the
amount model. The decomposed read keeps them separate — stage 60's
decomposition is not only about the tail, it is about letting each lever
be tuned and monitored on its own.

## Evidence boundary

The executed read over three declared cohorts (illustrative,
deterministic). It demonstrates the decomposition's independence; real
systems must validate that the rate and amount heads stay calibrated per
cohort after product changes.

## Check your mental model

Answer each before opening it.

**1. Why is regressing GMV directly a confound?**

<details>
<summary>Answer</summary>

Because GMV is a product, and a product's gradient cannot say which factor
moved. A change in AOV and a change in order rate look the same in the
target, so the model folds two mechanisms into one coefficient.

</details>

**2. What does the decomposition let a team do?**

<details>
<summary>Answer</summary>

Monitor and tune the rate and the amount separately: a flash sale should
move only the rate head, a pricing change only the amount head, so a
product change does not silently retrain the other model.

</details>

## Next

Back to [stage 60](../). The tail's own face: [the top 1% of orders own
25.4% of the gradient](../when-the-whale-dominates/).
