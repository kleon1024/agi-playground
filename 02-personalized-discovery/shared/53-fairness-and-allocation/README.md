---
status: verified
level: applied
base: scratch
label: Fairness and allocation
verified: 2026-08-07
---

# Exposure is a budget the ranker allocates

**Question:** stages 05-06 ranked for the user. This stage asks who else
the page belongs to, and answers: exposure is a budget the ranker
allocates — a click-optimal ranker gives most of it to the categories
that click best, and a fairness constraint reserves a share for the rest
at a measured price.

**Before this:** [stage 05 — value tree](../05-value-tree/) for the
objective the constraint shapes, and [stage 06 — mixing](../06-mixing/)
for the slate assembly this allocation lives in.

## The allocation, executed

The run ([record](runs/2026-08-07-fairness-and-allocation.md)) measures
exposure by category, unconstrained and under a 10% floor:

| category | ctr | unconstrained | with floor |
|---|---:|---:|---:|
| audio | 0.040 | 59% | 54% |
| video | 0.032 | 30% | 28% |
| cable | 0.022 | 10% | 9% |
| accessories | 0.010 | 1% | 9% |

Aggregate CTR: 0.0355 unconstrained, 0.0334 with the floor.

## The mechanism, named

The floor moves accessories from near-invisible to a real share and costs
a little aggregate CTR. Allocation is a constraint on the ranking
objective, and the price of the constraint is measured, not assumed:
exposure is the scarce resource the ranker distributes, so every fairness
decision is a budget decision about how much relevance the platform is
willing to spend on how visible a tail.

## Why this belongs in the mission

The mission ranks for a user but serves a marketplace: the page is also
the catalogue's marketplace, the creators' storefront, and the platform's
own allocation of what becomes popular. Stage 45 showed the feedback loop
concentrating exposure; this stage is the explicit lever against it — the
constraint that guarantees the tail stays reachable even when the head
clicks better. It is the same budget thinking as stage 50, applied to
exposure instead of compute.

## Evidence boundary

The executed allocation over four declared categories (illustrative,
deterministic). It demonstrates the mechanism; real fairness decisions
need the actual exposure distribution, the per-group objective, and the
measured cost of each constraint level — plus the group definitions
themselves, which are a policy decision.

## Check your mental model

Answer each before opening it.

**1. Why does the unconstrained ranker give accessories 1%?**

<details>
<summary>Answer</summary>

Because it optimizes clicks: accessories click at 0.010 against audio's
0.040, so the optimal slate shows them last and almost never. That is not
a bug — it is what a pure click objective does. The question is whether
the platform wants the objective to own the entire allocation, which is
what the floor answers.

</details>

**2. What does the floor actually buy?**

<details>
<summary>Answer</summary>

Reach: accessories go from 1% to 9% of exposure, so the category stays
visible enough to be discovered, learned from, and measured. The cost is
0.0021 aggregate CTR. Whether the reach is worth the clicks is the
allocation decision — and the constraint-bites detour shows the price is
a curve, not a flat rate.

</details>

## Next

The allocation is a measured trade; stage 54 follows the advertiser side
of the same budget. A detour from here: [the floor has a price and the
price is a curve](when-the-constraint-bites/) — the executed read: the
first ten points of floor move the tail from 1% to 9% for 0.0021 CTR; the
next ten cost more per point.

Another detour: [the label carries the position it was collected
in](when-the-policy-is-biased/) — the executed read: position-adjusted
CTR moves the tail from 14% to 36% of exposure, because the raw numbers
entrench the position bias.
