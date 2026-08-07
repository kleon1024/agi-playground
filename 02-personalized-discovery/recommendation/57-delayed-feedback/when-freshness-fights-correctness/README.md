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
