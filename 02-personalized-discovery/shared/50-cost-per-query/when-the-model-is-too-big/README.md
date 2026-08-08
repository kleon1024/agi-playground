---
status: verified
level: applied
base: scratch
label: When the model is too big
verified: 2026-08-07
---

# The model is too big when the last point of quality doubles the bill

**Question:** [stage 50's cascade](../) priced the query. This chapter
asks what a bigger model is worth, and answers: the last 0.01 of quality
has a price — doubling the fine-rank model buys a small NDCG gain at a
doubled cost per query, and whether it clears the budget is a decision,
not a foregone conclusion.

**Before this:** [stage 50 — cost per query](../) and its executed cascade
arithmetic.

## The upgrade, executed

The run ([record](runs/2026-08-07-model-is-too-big-read.md)) compares the
small and large fine-rank models over 10M queries/day:

| model | cost per query | ndcg | daily cost |
|---|---:|---:|---:|
| small | 1.0 units | 0.618 | 10,000,000 units |
| large | 2.0 units | 0.631 | 20,000,000 units |

## The reading

The large model adds 0.013 NDCG and doubles the daily cost of the
fine-rank stage. Whether that is worth it is a budget question: the same
units could buy recall depth, a cache, or a second experiment. Model size
is a cost line, and cost per query is the unit it is measured in. The
upgrade is not wrong — it is priced, and the price competes with every
other way to spend the same budget.

## The fix and its trade

The fix is to price the upgrade in cost-per-query units and compare it
against the other ways the same budget could be spent, instead of
shipping on the NDCG gain alone. The executed comparison prices the
choice — the small fine-rank model costs 1.0 units per query at NDCG
0.618 and the large one 2.0 units at 0.631, so 0.013 of quality doubles
the stage's daily bill from 10,000,000 to 20,000,000 units at 10M
queries.

The trade is that the gain is real but small, and the budget it spends
is not: the same 10M extra units a day could buy deeper recall, a cache
that cuts the whole cascade's cost, or a second experiment. Model size
is a cost line measured in the same unit capacity planning spends, so
the decision needs the measured live-traffic NDCG, the real per-query
cost delta, and the opportunity cost of the same budget elsewhere —
without those, the upgrade is an assertion, not a decision.

## Who owns the loop

- **The model team** owns the upgrade decision and must bring the
  measured NDCG on live traffic, not the benchmark number.
- **The measurement team** owns the real per-query cost delta and the
  opportunity-cost comparison against other budget uses.
- **The cost and finance owner** owns the budget line the per-query unit
  feeds, the same denominator capacity planning uses.

## Evidence boundary

The executed comparison over declared costs and NDCG values
(illustrative, deterministic). It demonstrates the trade; real upgrade
decisions need measured NDCG on the live traffic, the real per-query cost
difference, and the opportunity cost of the same budget elsewhere.

## Check your mental model

Answer each before opening it.

**1. What does the 0.013 NDCG gain actually buy?**

<details>
<summary>Answer</summary>

Nothing until it is priced: the same 10M units could buy a deeper recall
set, a cache that cuts the whole cascade's cost, or a second A/B
experiment. The gain is real but small, and the decision is whether the
measured lift clears the budget it spends — which is exactly the
opportunity-cost question the cache detour prices on the other side.

</details>

**2. Why is "cost per query" the right unit for this decision?**

<details>
<summary>Answer</summary>

Because it turns model size into a budget line that scales with traffic:
the large model's extra 1.0 unit becomes 10M extra units a day at 10M
queries. A one-off benchmark would call the gain "small"; the per-query
unit exposes that it doubles the stage's bill. Capacity planning (49)
spends this same unit, so model choice and machine sizing share one
denominator.

</details>

## Next

Back to [stage 50](../). The [cache-pays detour](../when-the-cache-pays/)
is the alternative the same budget could buy: cutting the whole cascade's
cost instead of improving one stage's quality.
