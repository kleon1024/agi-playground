---
status: verified
level: applied
base: scratch
label: When the slice trades
verified: 2026-08-07
---

# The first weight steps buy the tail cheaply, then the frontier saturates

**Question:** [stage 64's slice weighting](../) has a dial — the tail
weight. This chapter asks what each step of that dial actually buys and
sells, and where the frontier saturates, so the trade is made deliberately
instead of by accident.

**Before this:** [stage 64 — the slice that pays for the visible
objective](../), whose audit showed the tail slice paying for the head's
signal while the aggregate AUC read flat. This detour turns the fix into a
dial and reads every position on it.

## The dial, executed

The run ([record](runs/2026-08-07-slice-trades-read.md)) sweeps the tail
weight from 1.0 to 5.0 on the same cohort:

| tail weight | tail AUC | head AUC | aggregate AUC |
|---|---:|---:|---:|
| 1.0 | 0.654 | 0.673 | 0.735 |
| 2.0 | 0.682 | 0.638 | 0.725 |
| 3.0 | 0.695 | 0.621 | 0.717 |
| 4.0 | 0.702 | 0.609 | 0.710 |
| 5.0 | 0.708 | 0.602 | 0.704 |

## The reading

The first steps are the cheapest: weight 1.0 to 2.0 buys +0.028 of tail
AUC for a -0.035 head cost, and the aggregate barely moves. From 3.0 up,
each step buys less than the previous one — the frontier saturates around
a tail AUC of 0.71. Two consequences follow. First, the aggregate AUC is
not neutral, it is head-weighted: it falls monotonically (0.735 to 0.704)
while the tail gains, so watching it alone misreads a deliberate
reallocation as a regression. Second, where to sit on the frontier is a
product decision — the tail slice's experience against the head slice's —
that no single model metric decides. The model team can make the trade
possible; the product owner makes it.

## The fix and its trade

The failure is reading a reallocation as a regression: the aggregate AUC
is exposure-weighted, so it falls monotonically (0.735 to 0.704) while
the tail gains — watching it alone misreads a deliberate trade as the
model getting worse. The fix is the weight dial read per slice, and the
run measures every position on it: tail weight 1.0 to 5.0 moves tail AUC
from 0.654 to 0.708 and head AUC from 0.673 to 0.602. The trade is the
shape of the curve. The first steps are the cheapest — weight 1.0 to 2.0
buys +0.028 of tail AUC for a -0.035 head cost while the aggregate
barely moves — and the frontier saturates around a tail AUC of 0.71,
where each further step buys less than the last. The saturation point is
where the trade stops being a model question: the model team makes the
trade possible, and the product owner makes it.

## Who owns the loop

- **The model team** owns the dial and the measurement: the per-slice
  sweep that turns the fix into a curve.
- **The product owner** owns the frontier position: which slice's
  experience the system is buying is a product decision no single model
  metric can make.
- **The evaluation team** owns the guardrail: per-slice AUC with
  intervals on production slices, and the head slice's declared floor
  that a reallocation may not breach.

When ownership is implicit, the aggregate AUC is quoted in the
ship/reject meeting and the deliberate tail reallocation is rejected as
a regression.

## Evidence boundary

The executed synthetic sweep over one cohort with a declared head/tail
split (illustrative, deterministic, single seed). It demonstrates the
cheap-first-step shape and the saturation; real systems must read the
same curve on production slices, with per-slice intervals, before the
weight is chosen.

## Check your mental model

Answer each before opening it.

**1. Why does the aggregate AUC move at all, if the tail is a small
slice?**

<details>
<summary>Answer</summary>

Because the aggregate is exposure-weighted: the head slice owns most of
the rows, so head movement dominates it. The executed sweep shows the
aggregate falling monotonically as the tail weight rises — not a sign the
model got worse, but the head slice paying the bill. The aggregate cannot
show the reallocation because it never separates the two slices.

</details>

**2. Who decides where the dial stops?**

<details>
<summary>Answer</summary>

The product owner. The sweep measures the trade; it does not rank the two
experiences. The model team owns the dial and the measurement, and the
evaluation team holds the per-slice guardrail, but the position on the
frontier is a product decision about which slice's experience the system
is buying.

</details>

## Next

Back to [stage 64](../), where the stratified audit makes this trade
visible — now with the saturation point known in advance.
