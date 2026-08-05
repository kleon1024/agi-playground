---
status: verified
level: applied
base: none
label: When the trade weight moves
verified: 2026-08-06
---

# What does a mixing weight actually trade off?

**Question:** [stage 06](../) teaches two ways to shape a slate — a hard
category cap (a constraint you can point to) and a diversity decay (a penalty
weight that trades against value). Prose can say they are different promises;
this chapter measures the price of each on the stage's own catalogue, and the
shape of the ad-displacement curve the stage's trade rate controls.

**Before this:** [stage 06's slate assembly](../), its beam search, and the
recorded exhaustive optimum.

## The price of diversity, measured

The ablation runs the stage's own beam search on its own synthetic catalogue
(same seed, same value function) across the diversity-decay knob. Two numbers
matter at each setting: the value the optimizer maximized, and the raw value
at decay 1.0 — the underlying utility with the penalty removed.

| decay | categories | raw value | raw vs no-penalty |
|---:|---|---:|---:|
| 0.00 | cooking 1, music 1, news 1, sports 2 | 2.1853 | -0.1782 |
| 0.25 | cooking 1, music 1, news 1, sports 2 | 2.1853 | -0.1782 |
| 0.50 | cooking 1, music 1, news 1, sports 2 | 2.1853 | -0.1782 |
| 0.75 | cooking 1, music 1, news 1, sports 2 | 2.2011 | -0.1624 |
| 1.00 (no penalty) | cooking 1, news 1, sports 3 | 2.3634 | +0.0000 |

The no-penalty optimum is three sports items — maximum raw value, zero
diversity. The penalty buys diversity at a measured cost: 0.1782 raw value at
the stage's default 0.5. That is the trade a penalty weight makes, and it is
the reason stage 06 calls it indefensible: nothing in the number says whether
the 0.1782 was worth it.

The hard constraint is the surprise. With cap=2 the same beam search returns
raw value **2.2624** — higher than the default penalty's 2.1853 — and it is
a guarantee you can point to ("never more than two sports items"). On this
catalogue the constraint dominates the penalty on both axes: it keeps more
raw value *and* it is a promise. The chapter does not claim that generalizes;
it says the two mechanisms are not interchangeable, and here is the
arithmetic that shows which is cheaper on one catalogue.

The full sweep, the constraint reference, and the command are in
[`runs/2026-08-06-trade-weight-ablation.md`](runs/2026-08-06-trade-weight-ablation.md).

## Where the ad curve bends

The stage's trade rate converts expected ad revenue into the same utility
scale as organic value. Sweeping it on the fixed catalogue shows the curve's
knee:

| trade rate | revenue (load 4) | organic value displaced | revenue per displaced dollar |
|---:|---:|---:|---:|
| 0.5 | 0.000 | 0.0000 | — |
| 1.0 | 0.872 | 0.7821 | 1.11 |
| 2.0 | 1.423 | 1.2659 | 1.12 |
| 3.0 | 1.423 | 1.2659 | 1.12 |
| 5.0 | 1.885 | 2.0264 | 0.93 |
| 10.0 | 1.885 | 2.0264 | 0.93 |

Below rate 3, the fixed ads cannot cross the weakest organic slot, so nothing
is displaced. Between 3 and 5, the remaining ads start pushing the *strong*
organic items out: revenue grows 1.423 to 1.885 while displaced value grows
1.266 to 2.026, and the revenue-per-displaced-dollar falls from 1.12 to 0.93.
That fall is the knee — the point where each additional revenue dollar costs
more user value than the last one did. Stage 06's job is to make this curve
visible; where a business sits on it is a business decision. This chapter's
job is to show the knee is a real, measured shape, not a metaphor.

## Evidence boundary

This run measures one synthetic catalogue at one seed, reusing the stage's
own fixtures. It shows the constraint beating the penalty on this catalogue
and the ad knee existing here; it does not show either generalizes to real
catalogues, real user value, or real auction prices. No number in this
chapter is a business recommendation.

## Check your mental model

Answer each before opening it.

**1. Why does the constraint (cap=2) return more raw value than the default
penalty (decay 0.5) on this catalogue?**

<details>
<summary>Answer</summary>

Because the two mechanisms spend differently. The penalty discounts repeated
categories inside the value function, so the optimizer trades raw value for
diversity continuously and can still pick a suboptimal mix. The constraint
removes whole slates from consideration, which forces the search to find the
best slate that obeys the promise — on this catalogue that slate happens to
be worth 2.2624 raw, above the penalty's 2.1853. A constraint can be cheaper
than a penalty, and it is also a promise you can point to.

</details>

**2. What changes at the ad knee between trade rates 3 and 5?**

<details>
<summary>Answer</summary>

Below rate 3 the ads cannot outbid the weakest organic slot, so nothing is
displaced and revenue stops at what the cheapest ads buy. Above it, the
strongest organic items start being pushed out: revenue per displaced dollar
falls from 1.12 to 0.93 because each added ad now displaces a high-value
organic item instead of a low-value one. The knee is where marginal revenue
starts costing more user value than it did before.

</details>

## Next

Back to [stage 06's mixing](../), or forward to
[stage 07's rule engine](../../07-rule-engine/) where constraints with owners
live on a policy timescale.
