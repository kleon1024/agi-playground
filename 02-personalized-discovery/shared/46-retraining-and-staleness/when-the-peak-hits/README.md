---
status: verified
level: applied
base: scratch
label: When the peak hits
verified: 2026-08-07
---

# A calendar retrain misses the spike; an error trigger does not

**Question:** [stage 46's staleness](../) measures how fast the snapshot
ages. This chapter asks who decides *when* to retrain and answers: a
fixed cadence spends its retrains on the calendar, so a demand spike
lands between retrains and the stale order is served through the peak —
while a trigger that watches the measured error spends the same budget
on the world.

**Before this:** [stage 46 — retraining and staleness](../) and its
executed aging-snapshot read, plus [stage 47 — monitoring and
drift](../../47-monitoring-and-drift/) for the error signal a trigger
consumes.

## The spike, executed

The run ([record](runs/2026-08-07-peak-hits-read.md)) drives a demand
spike at hours 8-12 that flips two pairwise orderings, and compares two
schedulers:

| hour | calendar | adaptive |
|---|---:|---:|
| 8-11 | 2 | 2 then 0 |
| 12 | 0 (scheduled retrain) | 0 |
| 13-14 | 2 | 2 then 0 |

Calendar: 2 retrains, 12 error-hours. Adaptive: 3 retrains, 4
error-hours. Both peak at 2 wrong pairs; the difference is *when* the
error is served.

## The reading

The calendar retrained at hour 12 — mid-spike. It served the stale order
for every spike hour (8-11) and again after the spike ended (13-14),
because its hour-12 snapshot captured the spiked world and the world
snapped back an hour later. The trigger retrained at hour 8, the first
hour the spike became measurable, and at hour 13, the first hour the
world returned — holding stale exposure to one hour per change. It
cost one extra retrain and bought a threefold reduction in stale
exposure.

The retraining decision is the when, not the count. A cadence is a
convenience: it is easy to schedule and easy to reason about, but it
spends the compute budget on the calendar. An error trigger spends the
budget on the world: it needs the measured error per hour, which is
exactly the panel stage 47 builds, and it retrains when the measurement
changes, not when the clock does. Verachtert, Jeunen, and Goethals
("Scheduling on a budget: Avoiding stale recommendations with timely
updates", Machine Learning with Applications, 2023) formalize the same
decision: schedule retraining to maximize accuracy within a fixed
resource budget, and derive the staleness rate from the data rather than
assuming it.

## Evidence boundary

The executed spike over six declared items (illustrative, deterministic).
It demonstrates the mechanism; real systems must weigh the retrain cost
(compute, pipeline load, cache invalidation) against the error-hours
served, per cohort, and must decide how aggressive the trigger can be
before the retrains themselves destabilize the system.

## Check your mental model

Answer each before opening it.

**1. Why does the calendar serve the wrong order after the spike ends?**

<details>
<summary>Answer</summary>

Because its hour-12 retrain captured the spiked world: the volatile
cohort's boosted rates are baked into the snapshot. At hour 13 the boost
drops, the world snaps back, and the snapshot now disagrees with it —
the same two pairs rank wrong in the other direction. The calendar
missed the spike on the way in and on the way out.

</details>

**2. What does the error trigger need that the calendar does not?**

<details>
<summary>Answer</summary>

An hourly measurement of rank error against current truth, computed from
live labels — the prediction-observation gap panel of stage 47. The
calendar needs only a clock; the trigger needs an instrument, and the
instrument's noise budget decides how aggressive the trigger can be
without retraining on jitter.

</details>

## Next

The trigger needs the measured error; [stage 47 — monitoring and
drift](../../47-monitoring-and-drift/) builds the online panel that
produces it, and asks who owns the alert and the rollback when the panel
fires.
