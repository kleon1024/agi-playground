---
status: verified
level: applied
base: scratch
label: When freshness fights correctness
verified: 2026-08-07
---

# The freshest snapshot is the most censored

**Question:** [stage 57](../) fixes the label with a soft label for
in-flight rows. This chapter asks what happens when the training snapshot
is deliberately young, and answers: a snapshot that is mostly young rows is
mostly in-flight rows, so the naive model eats its false negatives exactly
where it is trying to be freshest.

**Before this:** [stage 57 — delayed feedback](../).

## The young snapshot, executed

The run ([record](runs/2026-08-07-freshness-fights.md)) trains on a fresh
snapshot (0.3-2 days) with and without the correction:

| model | conv AUC |
|---|---:|
| naive on fresh rows | 0.712 |
| corrected fresh rows | 0.732 |

in-flight converters in the training rows: 733.

## The reading

Retraining cadence is not the lever; the label correction is. Reweighting
the in-flight rows by their remaining conversion mass recovers the ranking
without waiting for maturity, so a team that wants fresher models does not
have to choose between staleness and lying labels. This is the same soft
label as stage 57, applied to the freshness axis: keep all the rows, correct
the ones whose outcome is not final.

## The fix and its trade

The fix is to reweight the in-flight rows by their remaining conversion
mass instead of waiting for maturity — retraining cadence is not the
lever, the label correction is. The executed read on a 0.3-2 day snapshot
prices it: the corrected model reaches 0.732 against 0.712 naive on the
same fresh rows, with 733 in-flight converters sitting inside the training
set either way.

The trade is that remaining conversion mass is an estimate with an
expiration date. It is computed from the current delay distribution, and
the moment the product changes the conversion funnel — a new step, a
different market — the estimate is wrong and the soft label starts lying
in the direction the product changed. The correction buys freshness without
staleness, but it makes the label pipeline the freshness owner: a team
that wants fresher models now depends on the delay estimator being
re-measured, not on the retraining platform running more often.

## Who owns the loop

- **The label pipeline team** owns the remaining-conversion-mass
  estimator and its re-check when the funnel changes — the soft label's
  correctness is a label-time property, not a training-time one.
- **The retraining platform team** owns the snapshot cadence decision and
  the trade it contains: how young the snapshot is allowed to be is now a
  label-pipeline input, because a young snapshot is a mostly-in-flight
  one.
- **The model team** owns applying the correction at train time and
  reading the corrected model on fresh rows — the AUC on the young
  snapshot is the acceptance metric.
- **The evaluation team** owns the naive-versus-corrected comparison on
  the same snapshot, so a freshness change is never confused with a
  quality change.

## Evidence boundary

The executed read over the young-snapshot synthetic stream (illustrative,
deterministic). It demonstrates the mechanism; real systems must estimate
remaining conversion mass from the actual delay distribution and re-check
it when the product changes the conversion funnel.

## Check your mental model

Answer each before opening it.

**1. Why does freshness make the naive model worse, not better?**

<details>
<summary>Answer</summary>

Because young rows are disproportionately in-flight rows. A snapshot that
is fresher is therefore more censored: the model gets the most up-to-date
impressions and the least-final labels at the same time.

</details>

**2. What does the correction change, concretely?**

<details>
<summary>Answer</summary>

It stops treating every in-flight converter as a negative. Each such row
carries a soft label proportional to its remaining conversion mass, so the
model can use the row without believing the false negative.

</details>

## Next

Back to [stage 57](../). The window's other failure: [too short a window
halves the AUC](../when-the-window-is-too-short/).
