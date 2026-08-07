---
status: verified
level: applied
base: scratch
label: Retraining and staleness
verified: 2026-08-07
---

# Retraining is a question of noticing the snapshot stopped paying

**Question:** stages 44-45 showed the world moving under the model. This
stage asks how often to retrain, and answers: rank error grows with the
age of the snapshot, so the question is not whether to retrain — the
world moves — but how to notice that the snapshot has stopped paying.

**Before this:** [stage 44 — training-serving
consistency](../44-training-serving-consistency/) for the skew retraining
responds to, and [stage 16 — CTR calibration](../../ads/16-ctr-calibration/) for
the estimates the stale model carries.

## The aging snapshot, executed

The run ([record](runs/2026-08-07-retraining-and-staleness.md)) evaluates
item click rates that drift over hours, counting pairwise rank errors
against the current truth:

| snapshot | evaluated at | wrong pairs |
|---|---|---:|
| hour 0 | hour 0 | 0 |
| hour 0 | hour 6 | 5 |
| hour 0 | hour 12 | 6 |
| hour 6 | hour 12 | 1 |

## The mechanism, named

Rank error grows from 0 at hour 0 to several wrong pairs at hour 12: the
model trained at hour 0 ranks the world as it was at hour 0. A snapshot
from hour 6 cuts that error to a single pair. Retraining on a newer
snapshot buys the error back — but only if the platform notices the old
snapshot stopped paying. Staleness is measured by the gap between the
model's world and the current one, and the retraining cadence is set by
how fast that gap grows, not by a calendar.

## Why this belongs in the mission

Every stage of the cascade holds a snapshot: the features (43), the
labels (44), the estimates (16), and now the model itself. Staleness is
the shared failure mode of all four, and this stage names the metric that
decides when each one is due: the measured error against current truth.
Without it, the mission's offline claims silently age into descriptions
of a world that ended.

## Evidence boundary

The executed drift over three declared hours (illustrative,
deterministic). It demonstrates the mechanism; real systems must measure
their own rank error against live labels, per cohort and per feature, and
set the retraining trigger against that measurement.

## Check your mental model

Answer each before opening it.

**1. Why does the error grow from 0 to 6 instead of staying flat?**

<details>
<summary>Answer</summary>

Because the item rates drift and the model holds the hour-0 snapshot. At
hour 0 the snapshot is the truth by construction, so the error is 0;
every hour after, the truth moves away and more pairs rank wrong. The
error is not a model-quality number — it is an age-of-snapshot number.

</details>

**2. What does the hour-6 snapshot prove?**

<details>
<summary>Answer</summary>

That retraining pays: evaluated at hour 12 it has only 1 wrong pair
against 6 for the hour-0 model. The comparison is the whole decision —
the platform does not need a calendar, it needs the measured gap, and the
retraining cadence is set by how fast that gap grows.

</details>

## Next

The snapshot ages; stage 47 builds the online panel that notices. A
detour from here: [the retrain that flips the metric offline can lose
online](when-retraining-flips-the-metric/) — the executed read: offline
NDCG rises 0.917 to 1.000 while exposure-weighted CTR falls.

Another detour: [the embedding expires and recall dies with
it](when-the-embedding-expires/) — the executed read: stale vectors give
recall 2/3, refreshed vectors 3/3, because retrain must reach the index,
not just the weights.
