---
status: verified
level: applied
base: scratch
label: When the creative is stale
verified: 2026-08-07
---

# Logged CTR mixes quality with wear

**Question:** [stage 26's creative selection](../) picks the creative
an ad shows. This chapter reads the executed wear comparison and asks
what logged CTR hides.

**Before this:** [stage 26 — creative selection](../) and its executed
per-context CTR model.

## The wear, executed

The run ([record](runs/2026-08-07-stale-creative-read.md)) reads three
creatives with their exposure histories:

| creative | logged CTR | exposure |
|---|---:|---|
| creative_a | 0.06 | 200,000 impressions |
| creative_b | 0.04 | mature |
| creative_c | 0.03 | new (cold start) |

## The reading

Logged CTR mixes the creative's quality with its wear. creative_a's
0.06 reflects 200,000 exposures — users have seen it, and its true
value has decayed below the log. creative_c's 0.03 is a cold-start
estimate with no wear history. A selection model that averages logged
CTR keeps choosing the stale winner on history while its actual value
falls, and never gives the new creative the traffic it needs to
estimate. Selection needs recency-aware estimates, not just averages.

## Evidence boundary

The executed comparison over three declared creatives (illustrative,
deterministic). It demonstrates the confound; real systems model
creative wear per segment and use exploration (traffic allocation) to
keep cold-start estimates honest.

## Check your mental model

Answer each before opening it.

**1. Why is creative_a's 0.06 not its true value?**

<details>
<summary>Answer</summary>

Because the log mixes quality with wear. creative_a earned that 0.06
partly because it was fresh; after 200,000 exposures its marginal click
rate has decayed, but the average still carries the early high-rate
history. The average overstates what a new impression of creative_a is
worth now.

</details>

**2. What does a cold-start creative need?**

<details>
<summary>Answer</summary>

Traffic to estimate — which a pure average-based selection never gives
it, because it always loses to the stale winner. Selection needs an
exploration allocation (some impressions for new creatives) and
recency-aware estimates, or the system locks onto yesterday's winner
forever.

</details>

## Next

Back to [stage 26](../), where the creative is part of the ad's value.
The [context detour](../when-the-creative-context-changes/) shows the
second confound: the same creative's value also changes per placement.
