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

## How you find it: the protected group, executed

A declared floor is not the same as the exposure the protected group
receives. The run ([record](runs/2026-08-07-fairness-and-allocation.md))
sweeps the floor level and emits the protected-group rows, and the audit
([record](runs/2026-08-07-allocation-audit.md) —
[`prod/allocation_audit.py`](prod/allocation_audit.py)) compares each
floor's declared level against the group's measured exposure, the way a
marketplace team reads allocation telemetry:

| floor | group exposure | gap | aggregate ctr |
|---|---:|---:|---:|
| 0% | 0.9% | −0.9% | 0.0355 |
| 5% | 4.8% | +0.2% | 0.0345 |
| 10% | 9.2% | +0.8% | 0.0334 |
| 15% | 12.6% | +2.4% | 0.0319 |
| 20% | 15.5% | +4.5% | 0.0307 |

The verdict is GROUP GAP: the gap between the declared floor and the
protected group's exposure grows with the floor level, because
renormalising after flooring the other categories re-dilutes the group
the floor was meant to protect. The configured constraint is not the
served allocation — measure per-group exposure, not the declared floor,
and fix the allocation by solving the constrained problem with the floor
binding, not by max-then-renormalise. Multi-sided exposure bias work
frames exactly this gap between the intended and the served allocation
(Abdollahpouri et al., "Multi-sided Exposure Bias in Recommendation",
KDD Workshop on Industrial Recommendation Systems 2020).

## The fix and its trade

The fix is to solve the constrained allocation with the floor binding
instead of max-then-renormalise, and to measure the protected group's
served exposure rather than the declared floor. The audit prices the
repair — a declared 10 percent floor lands at 9.2 percent served (gap
+0.8 percent), and the gap grows with the floor level because
renormalising the floored categories dilutes the group the floor was
meant to protect: at a 15 percent floor only 12.6 percent is served
(+2.4 percent). The per-group exposure telemetry, not the dashboard
floor, is the number the policy team routes on.

The trade is that the floor has a measured price, and the group
definition decides whether the constraint even binds. The first ten
points of floor move the tail from 1 percent to 9 percent of exposure
for 0.0021 aggregate CTR (0.0355 to 0.0334), and the next ten cost more
per point — the constraint-bites detour shows the price is a curve, not
a flat rate. The fairness verdict itself flips with the definition: the
tail clears its 10 percent floor across the catalogue (10.1 percent)
while the mobile segment, 70 percent of traffic, leaves it at 8 percent
— so who counts as the protected group is a policy decision made before
the measurement, and the position-bias detour shows the raw labels can
entrench the allocation further (position-adjusted CTR moves the tail
from 14 to 36 percent of exposure).

## Who owns the loop

The allocation only stays fair if someone owns each side of the budget,
and the handoffs are where the stage's failure modes live:

- **The ranking team** owns the served allocation: the exposure each
  group actually receives per floor level, and the fix when the
  constraint does not bind. It owns the served side of the budget.
- **The policy or product team** owns the group definitions and the
  floor levels: who the constraint protects, and the price the platform
  is willing to pay. It owns the intended side of the budget, and the
  when-the-groups-cross detour shows why the definition is a policy
  decision, not a reporting detail.
- **The measurement team** owns per-group exposure telemetry: the split
  that exposes the gap between the declared floor and the served
  allocation, and the fairness report that both definitions feed. It
  owns the verdict the policy team routes on.

When the ownership is implicit, each side optimizes its own number: the
ranking team tunes CTR, the product team sets floors from the dashboard,
and nobody measures the protected group's actual exposure — so the
constraint quietly fails to bind, the tail stays below the bar, and the
platform reports the floor it configured instead of the exposure it
served.

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

**3. Why does the declared 10% floor land as 9.2% for accessories?**

<details>
<summary>Answer</summary>

Because the max-then-renormalise implementation floors every category
and then rescales, so the floored categories push the protected group
back down: at a 10% floor, audio (59%) is untouched, cable is lifted to
10%, accessories to 10%, and the renormalisation shrinks accessories to
9.2%. The gap grows as the floor rises because more categories get
floored and the rescale dilutes harder. The fix is to solve the
constrained allocation with the floor binding, and to measure the served
exposure — not the configured number.

</details>

## Next

The allocation is a measured trade; stage 54 proves the allocation's
effect on users, and the ads track's
[advertiser ROAS](../../ads/56-advertiser-roas/) follows the advertiser
side of the same budget. A detour from here: [the floor has a price and the
price is a curve](when-the-constraint-bites/) — the executed read: the
first ten points of floor move the tail from 1% to 9% for 0.0021 CTR; the
next ten cost more per point.

Another detour: [the label carries the position it was collected
in](when-the-policy-is-biased/) — the executed read: position-adjusted
CTR moves the tail from 14% to 36% of exposure, because the raw numbers
entrench the position bias.

A third detour: [the fairness verdict flips with the
definition](when-the-groups-cross/) — the executed read: the tail clears
its 10% floor across the catalogue (10.1%) while the mobile segment,
70% of traffic, leaves it at 8% — the group definition decides the
verdict, so it is a policy decision, not a reporting detail.
