---
status: verified
level: applied
base: scratch
label: When the new user is the majority
verified: 2026-08-07
---

# The traffic that cannot be personalized

**Question:** [stage 23's personalized search](../) re-ranks with user
history, and the aggregate lift looks healthy. This chapter reads the
executed traffic-mix arithmetic and asks who the aggregate actually
describes — and what the model ships for the users it cannot help.

**Before this:** [stage 23 — personalized search](../) and its executed
relevance-plus-affinity model.

## The traffic mix, executed

The run ([record](runs/2026-08-07-new-user-majority-read.md)) splits a
traffic mix by history depth and applies each slice's measured lift:

| user slice | traffic | lift |
|---|---:|---:|
| new (no history) | 70% | +0.000 |
| light history | 20% | +0.020 |
| heavy history | 10% | +0.150 |
| aggregate | 100% | +0.019 |

## The reading

The aggregate lift +0.019 is a weighted average over sessions, and 70%
of those sessions have no history — the model cannot personalize them,
so they contribute zero to the average while dragging the headline
number toward "no effect". The benefit is concentrated in the 10% who
benefit most. Dou, Song and Wen ("A Large-scale Evaluation and
Analysis of Personalized Search Strategies", WWW 2007) measure the same
shape at scale: personalization gains depend on the user and the query,
with head queries and low-history users gaining little. The product
decision is not the lift on the heavy slice — it is the cold-start
policy: what do the 70% see before there is any history to personalize
with? A popularity or query-only prior, not a bigger model.

This is also the measurement discipline the stage's own
[lift audit](../runs/2026-08-07-personal-audit.md) encodes: report the
lift per slice, and check the traffic share of each slice, because the
aggregate hides exactly this concentration.

## Evidence boundary

The executed traffic-mix arithmetic over three illustrative slices
(deterministic). It demonstrates the aggregation trap; real traffic
mix and per-slice lift come from the production log.

## Check your mental model

Answer each before opening it.

**1. How can the aggregate lift hide that most users gain nothing?**

<details>
<summary>Answer</summary>

Because the aggregate is an average over sessions. If 70% of sessions
belong to users with no history, their zero lift is baked into the
mean, and the positive lift of the 30% who can be personalized is
diluted to a small headline number — or worse, a flat one that hides
the concentration in both directions.

</details>

**2. What should the team optimize instead of the aggregate lift?**

<details>
<summary>Answer</summary>

The cold-start policy for the no-history majority: what ranking they
see before any history exists. The personalization model only pays off
on the history-bearing slice; the product decision that moves the
whole traffic curve is what the other 70% get.

</details>

## Next

Back to [stage 23](../), where personalization is context added to the
query. The [history-helps detour](../when-the-user-history-helps/)
covers the prior at work; this chapter covered the majority that has no
prior to use.
