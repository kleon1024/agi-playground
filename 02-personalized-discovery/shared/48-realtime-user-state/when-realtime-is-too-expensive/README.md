---
status: verified
level: applied
base: scratch
label: When realtime is too expensive
verified: 2026-08-07
---

# Realtime is too expensive once every feature is on the critical path

**Question:** [stage 48's session](../) re-ranks the slate. This chapter
asks what each realtime feature costs, and answers: every live feature is
a millisecond on the request path, and at some count the realtime state
stops paying for itself.

**Before this:** [stage 48 — realtime user state](../) and its executed
session-boost read, plus [stage 08 — serving](../../08-serving/) for the
100ms-class deadline.

## The latency sweep, executed

The run ([record](runs/2026-08-07-realtime-is-too-expensive-read.md))
measures the p95 per request as realtime features are added, against a
100ms deadline:

| realtime features | p95 | verdict |
|---|---:|---|
| 0 | 38ms | ok |
| 5 | 58ms | ok |
| 10 | 78ms | ok |
| 20 | 118ms | over |

## The reading

The batch path alone sits at 38ms. Ten realtime features push the p95 to
78ms — still inside the deadline; twenty blow through it. Every feature
added to the request path is a latency budget spent, and the ones whose
signal does not change minute to minute belong in the batch path, not on
the critical one. The hybrid is not a compromise — it is the accounting:
put a feature live only when its freshness beats the latency it costs.

## Evidence boundary

The executed sweep over a declared p95 model (illustrative,
deterministic). It demonstrates the mechanism; real systems must measure
each realtime feature's latency and lift on the live path, and re-run
the accounting as the deadline or the model changes.

## Check your mental model

Answer each before opening it.

**1. Why does the batch path sit at 38ms before any realtime feature?**

<details>
<summary>Answer</summary>

Because it reads precomputed state — learned priors and batch features
that were computed once and stored. Nothing on that path is computed per
request, so the baseline is the model's own cost. Realtime features add
per-request computation on top, which is why the p95 climbs with the
count.

</details>

**2. Where is the line between live and batch?**

<details>
<summary>Answer</summary>

At the signal's freshness: a feature whose value changes minute to minute
justifies the request-path spend; one that changes hourly does not. The
same feature can cross the line as the deadline tightens — the detour's
20-feature case is fine for a 200ms budget and fatal for 100ms. The line
is a budget decision, re-measured, not a fixed list.

</details>

## Next

Back to [stage 48](../). The [session-state-moves
detour](../when-the-session-state-moves/) shows the other side of the
same trade: the boost that decays as the view recedes, and the batch
order that wins back.
