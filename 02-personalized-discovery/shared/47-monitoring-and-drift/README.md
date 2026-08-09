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

<!-- interactive: MonitoringDrift -->

## The mechanism, named

The model kept predicting 0.040 while users clicked less every hour. The
offline eval cannot see this — its labels come from the same broken
world, so an eval on those labels stays flat while the live page
collapses. The prediction-observation gap, smoothed and tracked online,
is what changes: it crosses the alert threshold at hour 10 while nothing
in the offline harness moved. Monitoring lives online, not in the eval
harness, because the eval and the model share their blindness.

## How you find it: the slice-aware drift panel, executed

The gap panel catches the break that moves the aggregate. The failure
mode it misses is the break that does not: when the defect is confined
to a small traffic segment, the diluted aggregate stays under threshold
while the slice collapses. The run ([record](runs/2026-08-07-monitoring-and-drift.md))
emits the hourly trace plus per-slice observed series, and the panel
applies the same EWMA gap check per slice:

| slice | traffic share | observed | final gap | alert |
|---|---:|---:|---:|---:|
| aggregate | diluted | 0.040 → 0.037 | 0.003 | never |
| homepage | 90% | 0.040 → 0.039 | 0.001 | never |
| category-a | 6% | 0.041 → 0.010 | 0.030 | hour 10 |
| new-users | 4% | 0.040 → 0.033 | 0.007 | never |

The verdict is HIDDEN SLICE: the aggregate never crossed the threshold
while category-a collapsed to a tenth of its rate and alerted at hour
10. A flat aggregate is not proof that the page is fine — it is a
promise to slice. The same drift taxonomy Gama et al. survey ("A Survey
on Concept Drift Adaptation", ACM Computing Surveys, 2014) applies per
slice: the drift that is invisible at the page level is visible at the
segment level, and the slice definition decides whether the collapse is
findable at all. The panel's thresholds are the TFDV-style validation
the pipeline already runs on features (Breck et al., "Data Validation
for Machine Learning", SysML 2019), applied to the outcome gap instead
of the input distribution: per-environment, per-slice, with a threshold
that names the segment, not just the page.

## The fix and its trade

The fix is an online prediction-observation gap panel, per slice, with
a named rollback authority on the other end of the alert. The executed
trace prices the repair — the model predicts 0.040 while observed CTR
falls to 0.020, and the EWMA crosses the threshold at hour 10 while
offline NDCG stays flat at 0.712 because the eval shares the broken
world — and the slice panel catches what the aggregate dilutes:
category-a collapses to 0.010 (gap 0.030) and alerts at hour 10 under an
aggregate gap of 0.003 that never fires.

The trade is that the panel's thresholds are a false-alarm-versus-
latency budget, and the slice definition decides whether the failure is
findable at all. A tight threshold catches the break but fires on noise —
at +/-0.002 the panel fires for seven hours — while a loose one waits
until the break is unmistakable. Small slices carry their own noise: a
500/day segment's daily test fires twice on noise and detects a real 50
percent drop three days late, where a 14-day pooled window detects
reliably at the price of latency. The panel names the slice, but the
rollback authority owns what happens at hour 10, and without that named
owner the alert fires into a vacuum.

## Who owns the loop

The panel produces a signal; someone must own what happens next, and the
handoff is where monitoring fails:

- **The monitoring team** owns the panel and the alert: slice
  definitions, thresholds, smoothing, and the false-alarm budget
  (the when-the-alert-is-noisy detour). It owns the instrument, not the
  fix.
- **The rollback authority** owns the decision to revert a serving
  change or force a retrain when the alert fires. This is a named
  owner, not a group chat: when the alert says the ranker broke at hour
  10, someone with the authority to pull the switch must exist at hour
  10.
- **The feature owner** owns the slice-level meaning: whether a
  category-a collapse is a data bug (the price feature returning zero,
  as in this stage's scenario), a product change, or a real demand
  shift. The panel names the slice; the feature owner names the cause,
  which decides whether the fix is a rollback, a retrain, or a
  recalibration.

When the ownership is implicit, the alert fires into a vacuum: the
monitoring team can name the slice, but nobody owns the rollback, so the
broken ranking runs until someone notices the pager and improvises.

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

**3. Why does the diluted aggregate stay flat while the slice dies?**

<details>
<summary>Answer</summary>

Because the 6% slice's collapse is diluted by the 90% slice that stayed
flat: the aggregate moves 0.040 to 0.037 (gap 0.003) while category-a
falls to 0.010 (gap 0.030). The page-level threshold is a weighted
average, and a weighted average cannot see a small segment's failure
until the segment is large enough to move it. That is why the panel is
per-slice, and why the slice definition decides whether the collapse is
findable.

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

A third detour: [the aggregate hides the slice; the slice's own noise
hides the fix](when-the-slice-hides/) — the executed read: a 500/day
segment's daily test fires twice on noise and detects a real 50% drop
three days late, while a 14-day pooled window detects reliably at the
price of latency.
