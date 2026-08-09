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

<!-- interactive: RetrainingStaleness -->

## The mechanism, named

Rank error grows from 0 at hour 0 to several wrong pairs at hour 12: the
model trained at hour 0 ranks the world as it was at hour 0. A snapshot
from hour 6 cuts that error to a single pair. Retraining on a newer
snapshot buys the error back — but only if the platform notices the old
snapshot stopped paying. Staleness is measured by the gap between the
model's world and the current one, and the retraining cadence is set by
how fast that gap grows, not by a calendar.

## How you find it: the per-cohort staleness panel, executed

The gap grows unevenly, and an aggregate number hides which cohort is
aging. The check that finds it builds the panel per cohort: for each
snapshot hour, how many pairwise orderings does it get wrong at each
later hour, split by how fast the cohort's rates move. The run
([record](runs/2026-08-07-staleness-panel.md)) emits the item table and
builds the panel:

| cohort | items | snap0 @ hour 6 | snap0 @ hour 12 | snap6 @ hour 12 |
|---|---:|---:|---:|---:|
| all | 6 | 5 | 6 | 1 |
| volatile | 4 | 2 | 2 | 0 |
| stable | 2 | 0 | 0 | 0 |

The verdict is VOLATILE FIRST: the fast-moving cohort already ranks two
pairs wrong at hour 6 while the stable cohort is still exact, so a
retraining trigger tuned to the aggregate average leaves the fast movers
stale longest. The aggregate row (5, 6, 1) is dominated by the volatile
cohort plus the cross-cohort pairs; the panel's job is to name which
cohort is due, because a single cadence for both cohorts is a
compromise nobody asked for. Verachtert, Jeunen, and Goethals
("Scheduling on a budget: Avoiding stale recommendations with timely
updates", Machine Learning with Applications, 2023) show the same
property from the data side: the rate at which a model becomes stale is
environment-dependent and derivable from the logs, so the trigger should
be derived from the measured error per cohort, not assumed by a
calendar.

## The fix and its trade

The fix is to derive the retraining trigger from the per-cohort staleness
panel instead of a calendar. The executed runs price the failure the fix
removes: a model snapshot ranks its own world exactly (0 wrong pairs at
hour 0) and then ages — 5 wrong pairs at hour 6, 6 at hour 12 — while a
snapshot from hour 6 holds the error to 1 pair at hour 12. The panel
names which cohort is due: the volatile cohort already ranks 2 pairs
wrong at hour 6 while the stable cohort is still exact, so a trigger
tuned to the aggregate leaves the fast movers stale longest. Verachtert,
Jeunen, and Goethals (2023) show the same property from the data side:
the rate at which a model becomes stale is environment-dependent and
derivable from the logs, so the trigger should be derived from measured
error per cohort, not assumed by a calendar.

The trade, named: retraining is a budget decision. An error trigger
buying freshness needs per-hour truth labels (stage 47's panel), a
compute budget for the retrains themselves, and pipeline, index-rebuild,
and cache-invalidation costs — the when-the-peak-hits detour prices the
purchase at one extra retrain for a threefold cut in stale exposure, and
the cost owner decides whether the purchase is worth it. When the
ownership is implicit, retraining is either too rare (the snapshot
silently ages) or too frequent (the platform retrains on noise and
spends the budget on jitter).

## Who owns the loop

Retraining is a budget decision, and the trigger sits at the handoff of
three owners:

- **The retraining platform** owns the trigger and the measurement: it
  runs the per-cohort panel above, holds the error budget, and decides
  when a cohort is due. The trigger is a platform service, not a model
  team's cron job.
- **The cost owner** owns the retrain's price — compute, pipeline load,
  index rebuild, cache invalidation — and sets how aggressive the
  trigger may be. The trade in the when-the-peak-hits detour is exactly
  this budget: one extra retrain bought a threefold cut in stale
  exposure, and the cost owner decides whether the purchase is worth it.
- **The monitoring team** owns the live labels the panel measures
  against. Without a per-hour truth signal (stage 47's gap panel), the
  trigger is blind and the calendar is the only option left.

When the ownership is implicit, retraining is either too rare (the
snapshot silently ages) or too frequent (the platform retrains on noise
and spends the budget on jitter). The trigger makes the handoff explicit
because it names the measurement, the budget, and the owner of each.

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

**3. Why is the aggregate panel not enough to set the trigger?**

<details>
<summary>Answer</summary>

Because the aggregate is dominated by the volatile cohort's errors, and
the stable cohort's exactness hides inside it. A trigger tuned to the
average either retrains the stable cohort too often (spending budget on
cohorts that are still exact) or lets the volatile cohort run stale
between retrains. The per-cohort panel names which cohort is due, which
is the information the trigger actually needs.

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

A third detour: [a calendar retrain misses the spike; an error trigger
does not](when-the-peak-hits/) — the executed read: through a demand
spike the calendar serves 12 error-hours and the trigger 4, for one
extra retrain.
