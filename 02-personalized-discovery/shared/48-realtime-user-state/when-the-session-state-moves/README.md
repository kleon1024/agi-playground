---
status: verified
level: applied
base: scratch
label: When the session state moves
verified: 2026-08-07
---

# The session boost decays and the batch order wins back

**Question:** [stage 48's session](../) re-ranks the slate at request
time. This chapter asks what the boost does as the session ages, and
answers: the realtime boost decays with the view's age, and the batch
model's learned order reasserts itself — the decay curve is where the
freshness-versus-stability decision lives.

**Before this:** [stage 48 — realtime user state](../) and its executed
session-boost read.

## The decay, executed

The run ([record](runs/2026-08-07-session-state-moves-read.md)) tracks
the audio boost's effect minutes after a view:

| minutes since view | boost | order |
|---|---:|---|
| 2 | 0.0097 | P1001, P1002, P1003, P1004, P1005 |
| 20 | 0.0015 | P1001, P1003, P1002, P1004, P1005 |
| 40 | 0.0002 | P1001, P1003, P1004, P1002, P1005 |

## The reading

Two minutes after the view the second audio item outranks the cable item
on the session boost; by twenty minutes the boost has decayed and the
batch order is back. The session state is not binary — its age is the
feature — and the decay curve is where the freshness-versus-stability
decision lives. A boost that never decays keeps the user trapped in one
mood; one that decays too fast never changes the page; the curve sets the
horizon of "recent" per surface.

## Evidence boundary

The executed decay over three declared read times (illustrative,
deterministic). It demonstrates the mechanism; real systems must set the
decay rate per signal and per surface, and measure whether the half-life
matches the user's actual return behavior.

## Check your mental model

Answer each before opening it.

**1. Why does P1002 fall below P1003 as the view ages?**

<details>
<summary>Answer</summary>

Because P1002's boost depends on the session, and the boost decays with
the minutes since the view. At 2 minutes the boost (0.0097) lifts P1002
above the cable item; by 20 minutes the boost is 0.0015, too small to
overcome P1003's higher learned CTR. The session stopped mattering before
the user left the page.

</details>

**2. What does the decay rate actually decide?**

<details>
<summary>Answer</summary>

The horizon of "recent": how long one view keeps steering the slate. Too
fast, and the realtime state is decorative — it never survives to the
next request; too slow, and a single mood owns the page for hours. The
right rate matches the surface's real return rhythm, which is measured,
not chosen by taste.

</details>

## Next

Back to [stage 48](../). The [realtime-cost
detour](../when-realtime-is-too-expensive/) is the other half of the
design: the latency each live feature spends on the request path.
