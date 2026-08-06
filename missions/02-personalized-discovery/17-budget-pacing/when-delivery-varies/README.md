---
status: verified
level: applied
base: scratch
label: When delivery varies
verified: 2026-08-06
---

# The cap that binds when demand spikes

**Question:** [stage 17's budget pacing](../) assumed a known demand
curve. This chapter reads the executed controller against unexpected
demand and asks what the cap actually does.

**Before this:** [stage 17 — budget pacing](../) and its executed
simulation.

## The response, executed

The run ([record](runs/2026-08-06-variance-read.md)) runs the pacing
controller (cap = 12.5) against demand that spikes to 30:

| hour | demand | spend | remaining |
|---:|---:|---:|---:|
| 0 | 30 | 12.5 | 87.5 |
| 1 | 28 | 12.5 | 75.0 |
| 2 | 25 | 12.5 | 62.5 |
| 3 | 20 | 12.5 | 50.0 |
| 4 | 15 | 12.5 | 37.5 |
| 5-7 | 10-2 | tapers | 27.5 -> 20.5 |

Total spent 79.5 of 100.

## Two readings

**The cap binds exactly when it is needed.** Demand exceeds the budget at
every early hour, and the cap holds spend flat at 12.5 while demand
spikes — the budget survives the day. Without the cap, naive spend would
have exhausted the budget in the first two hours.

**The remaining column is the feedback signal.** A production controller
does not just cap; it compares actual to planned delivery and re-paces —
loosen the cap if behind, tighten if ahead. The executed run shows the
fixed-cap outcome (20.5 unused at the end); the dynamic version uses that
remaining number to adjust, which is the difference between a rule and a
controller.

## Evidence boundary

The executed controller over one hand-built demand curve (illustrative,
deterministic, fixed cap). It demonstrates the cap's binding behavior;
real pacing also models bid price, competition, and the auction's win
rate, and re-paces against live delivery.

## Check your mental model

Answer each before opening it.

**1. Why does the cap hold spend flat even when demand triples?**

<details>
<summary>Answer</summary>

Because the cap is a per-hour ceiling: no matter how much demand arrives,
the controller spends at most budget/hours. At hour 0 demand is 30 but
spend is 12.5 — the cap rejects the surplus. That is the pacing mechanism:
it trades peak-hour volume for full-day presence, which is what the
advertiser's daily budget actually buys.

</details>

**2. What does the 20.5 unused mean for the design?**

<details>
<summary>Answer</summary>

That a fixed cap is conservative — it protects against overspend but
leaves budget on the table when late demand is lower than the cap allows.
A production controller treats this as feedback: the remaining column at
each hour says whether delivery is on plan, and the controller loosens or
tightens the cap accordingly. The unused budget is the cost of the simple
design and the input to the adaptive one.

</details>

## Next

Back to [stage 17](../), or to
[stage 18 — ad externality](../../18-ad-externality/) where delivery returns
to the mission's central trade.
