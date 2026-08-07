---
status: verified
level: applied
base: scratch
label: Monitoring and drift
verified: 2026-08-07
---

# Monitoring lives online because the offline eval reuses the broken world

**Question:** stage 46 measured the snapshot's age. This stage asks who
notices when the world breaks at serve time, and answers: the offline
eval cannot, because its labels come from the same broken world — the
prediction-versus-observation gap, tracked online, is the signal that
catches the regression nobody flagged.

**Before this:** [stage 46 — retraining and
staleness](../46-retraining-and-staleness/) for the aging snapshot, and
[stage 08 — serving](../08-serving/) for the path being monitored.

## The gap, executed

The run ([record](runs/2026-08-07-monitoring-and-drift.md)) tracks twelve
hours of predicted CTR (0.040) against observed CTR:

| hour | predicted | observed | gap | ewma |
|---|---:|---:|---:|---:|
| 0 | 0.040 | 0.039 | 0.001 | 0.000 |
| 4 | 0.040 | 0.036 | 0.004 | 0.001 |
| 8 | 0.040 | 0.023 | 0.017 | 0.011 |
| 10 | 0.040 | 0.022 | 0.018 | 0.015 ALERT |
| 11 | 0.040 | 0.020 | 0.020 | 0.016 ALERT |

## The mechanism, named

The model kept predicting 0.040 while users clicked less every hour. The
offline eval cannot see this — its labels come from the same broken
world, so an eval on those labels stays flat while the live page
collapses. The prediction-observation gap, smoothed and tracked online,
is what changes: it crosses the alert threshold at hour 10 while nothing
in the offline harness moved. Monitoring lives online, not in the eval
harness, because the eval and the model share their blindness.

## Why this belongs in the mission

The mission's evidence discipline ends at a measured outcome, and a
measurement is only as good as the instrument that keeps it honest.
Stages 43-46 built the pipeline's internal consistency; this stage builds
the external one — the live gap between what the system claims and what
users do. It is the last line of defence for every offline claim the
mission makes, and the panel that decides when a retrain (46) or a
rollback is due.

## Evidence boundary

The executed twelve-hour trace over a declared prediction (illustrative,
deterministic). It demonstrates the mechanism; real monitoring must set
thresholds against measured noise (the detour), choose the smoothing
window, and pair the gap with alerting that reaches a human.

## Check your mental model

Answer each before opening it.

**1. Why does the offline eval stay flat while the page collapses?**

<details>
<summary>Answer</summary>

Because its labels are collected from the same broken feed: if users
click less, the eval's labels shrink with the page, and NDCG on those
labels looks unchanged. The eval measures the model against its own
world; the gap panel measures the model against the user, which is the
comparison that actually moved here.

</details>

**2. Why does the EWMA alert at hour 10 and not hour 4?**

<details>
<summary>Answer</summary>

Because the raw gap jitters — hour 4's gap of 0.004 is within normal
noise. The EWMA smooths the series, so it only crosses the threshold once
the gap has been consistently large for several hours. The smoothing is
the same trade the noisy-alert detour measures: tight enough to catch the
break, calm enough not to fire on the jitter.

</details>

## Next

The gap panel is built; stage 48 asks what real-time state should ride on
the request path. A detour from here: [a threshold tight enough to catch
a break is tight enough to fire on noise](when-the-alert-is-noisy/) — the
executed read: at +/-0.002 the panel fires seven hours; at +/-0.010 it
waits until the break is unmistakable.

Another detour: [the drift is silent in the eval and loud in the
gap](when-the-drift-is-silent/) — the executed read: offline NDCG stays
at 0.712 across all twelve hours while observed CTR halves.
