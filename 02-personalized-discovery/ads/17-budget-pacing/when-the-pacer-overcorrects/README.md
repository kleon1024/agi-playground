---
status: verified
level: applied
base: scratch
label: When the pacer overcorrects
verified: 2026-08-07
---

# The pacer that fixes delivery by oscillating

**Question:** [stage 17's variance detour](../when-delivery-varies/) shows
a fixed cap and names the feedback signal. This chapter reads the
executed controller audit and asks what happens when the feedback gain
is too high.

**Before this:** [stage 17 — budget pacing](../) and its variance detour.

## The controller, executed

The run ([record](runs/2026-08-07-overcorrection.md)) re-paces against
cumulative deviation from plan — cap_next = target + gain x (planned -
actual) — over demand that alternates 20/2 per hour:

| gain | total spent | dark hours | hourly spend pattern |
|---|---:|---:|---|
| 0.5 | 95.7 | 0 | 12 2 14 2 14 2 14 2 15 2 15 2 |
| 1.0 | 100.0 | 1 | 17 2 15 2 15 2 15 2 15 2 15 0 |
| 3.0 | 100.0 | 6 | 20 0 20 0 13 0 20 0 13 0 13 0 |

## Two readings

**High gain turns pacing into oscillation.** At gain 0.5 the controller
spends something every hour and buys the cheap low-demand hours. At gain
3.0 any deficit floods the cap to the demand ceiling, any surplus clamps
it to 0 — the campaign alternates between flooding and going dark six
times in the day. The controller is tracking the plan, but the
correction is bigger than the error, so it never converges.

**The failure mode is the gain, not the feedback loop.** The variance
detour's fixed cap under-delivers; this read shows the opposite failure
on the same budget. A controller that reacts too hard converts a pacing
problem into an oscillation, and the measured signature is the dark-hour
count: 0 at gain 0.5, 6 at gain 3.0. Production pacing sits between the
two — gain high enough to recover from a demand shift, low enough not
to overshoot.

## The fix and its trade

The measured fix is to bound the feedback: cap the correction per hour,
react to smoothed (windowed) delivery instead of raw cumulative error,
and add a small deadband so small deviations do not move the cap
(Agarwal, Ghosh, Wei & You, 2014, KDD, pace via a delivery-rate control
that adjusts a probability of participating per auction; Xu et al., 2015,
KDD, formulate smart pacing as a constrained optimization solved per
request rather than a reactive rule). The trade is the one the table
shows: gain 0.5 leaves 4.3 of the budget unspent (slow response to a
permanent shift), gain 3.0 spends everything but darkens six hours
(overshoot). The controller's gain is tuned against the demand
volatility of the inventory, and the dark-hour metric is the alarm that
an oscillation has started (Wang, Zhang & Yuan, 2017, *Foundations and
Trends in Information Retrieval* 11(4-5), survey pacing and bidding
together as one delivery-control problem).

## Evidence boundary

The executed controller over a hand-built alternating demand pattern with
no random draws (illustrative, deterministic). It demonstrates the
overshoot mechanism; real pacing also models bid price, competition, the
auction's win rate, and measurement lag, which shift where the gain
starts oscillating.

## Check your mental model

Answer each before opening it.

**1. How can the same controller spend more and deliver worse?**

<details>
<summary>Answer</summary>

Because the spend is in the wrong hours. Gain 3.0 spends the full 100.0
but floods the high-demand hours and skips the cheap low-demand ones —
six hours dark. Gain 0.5 leaves 4.3 unspent but delivers every hour,
including the cheap ones. Delivery quality is a distribution over hours,
not a total; the dark-hour count is what separates the two.

</details>

**2. Your pacer's dark-hour count jumped. What do you change?**

<details>
<summary>Answer</summary>

The gain, and the signal it reacts to. Lower the correction so it does
not flood after one deficit, smooth the delivery measurement so the
controller reacts to a trend rather than an hour, and add a deadband so
small deviations are ignored. Then watch the dark-hour count and the
unspent budget together — the first falls as the second rises, and the
trade is the tuning problem.

</details>

## Next

Back to [stage 17](../), or to
[stage 18 — ad externality](../../18-ad-externality/) where delivery
returns to the mission's central trade.
