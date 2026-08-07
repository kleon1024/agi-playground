---
status: verified
level: applied
base: scratch
label: When the constraint bites
verified: 2026-08-07
---

# The floor has a price and the price is a curve

**Question:** [stage 53's allocation](../) priced the 10% floor. This
chapter asks what each further point of floor costs, and answers: the
floor has a price, and the price is a curve — the cost grows faster than
the floor, because the last few points buy the most visible allocation
and the most expensive clicks.

**Before this:** [stage 53 — fairness and allocation](../) and its
executed exposure-budget read.

## The floor sweep, executed

The run ([record](runs/2026-08-07-constraint-bites-read.md)) sweeps the
per-category floor:

| floor | tail exposure | aggregate ctr |
|---|---:|---:|
| 0% | 1% | 0.0355 |
| 5% | 5% | 0.0345 |
| 10% | 9% | 0.0334 |
| 20% | 15% | 0.0307 |

## The reading

The first ten points of floor move the tail from 1% to 9% and cost 0.0021
aggregate CTR; the next ten move it only to 15% and cost more (0.0027)
per point of exposure. The constraint curve is where the allocation
decision lives — how much relevance the platform is willing to spend on
how visible a tail. Diminishing returns run both ways: each additional
point of floor buys less tail reach and costs more aggregate clicks.

## Evidence boundary

The executed sweep over declared floors (illustrative, deterministic). It
demonstrates the mechanism; real constraints must be set against the
measured exposure curve and the platform's stated price for tail
visibility, re-measured as the catalogue or the objective changes.

## Check your mental model

Answer each before opening it.

**1. Why does the tail gain 8 points for the first 10 of floor and only 6
for the next 10?**

<details>
<summary>Answer</summary>

Because the floor starts by rescuing the most-starved category, where
every rescued slot is new reach; once the tail is visible, further floor
redistributes among already-visible categories, gaining less exposure per
point. The first points buy the cheapest visibility; the later ones buy
the most expensive, which is why the cost curve bends upward.

</details>

**2. What does the bend in the curve mean for the decision?**

<details>
<summary>Answer</summary>

That there is a knee — a floor level where further constraint stops being
worth its clicks. The decision is not "is fairness good", it is "where on
this curve does the platform sit", and the answer depends on how the
platform prices tail visibility against aggregate CTR. The curve is
measured, and the level is chosen against it.

</details>

## Next

Back to [stage 53](../). The [policy-biased
detour](../when-the-policy-is-biased/) is the measurement problem hiding
behind every allocation: the CTRs being ranked are themselves biased by
where the policy showed the items.
