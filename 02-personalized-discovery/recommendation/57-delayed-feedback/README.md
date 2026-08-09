---
status: verified
level: applied
base: scratch
label: Delayed feedback
verified: 2026-08-07
---

# A conversion that happens tomorrow is labeled a negative today

**Question:** stage 56 assumed the pay label is final when training
starts. This stage asks what happens when the label arrives late — a
user who will order tomorrow is in today's training set as a negative —
and answers: a young snapshot has no mature set to wait for, the naive
model under-reads fresh traffic, and the correction is a soft label from
the delay distribution, not a longer wait.

**Before this:** [stage 56 — entire-space funnel](../56-entire-space-funnel/)
for the funnel the labels describe, and [stage 47 — monitoring and
drift](../../shared/47-monitoring-and-drift/) for why the under-read looks like a
launch dip before anyone suspects the labels.

## The snapshot, executed

The run ([record](runs/2026-08-07-delayed-feedback.md)) simulates a
window of seven days, snapshot ages of 0.3 to 3 days, and a median delay
of about three days — so the snapshot is young on purpose:

| model | conv auc | predicted on fresh traffic |
|---|---:|---:|
| mature-only | starved (0 mature rows) | — |
| naive-all | 0.666 | 0.092 |
| corrected | 0.672 | 0.142 |

The true conversion-by-7 rate on fresh traffic is 0.132.

<!-- interactive: DelayedFeedbackWindow -->

## The mechanism, named

Conversion is observed only after its delay elapses, so at any snapshot
the freshest rows are the most likely to still be in flight: labeling
them negative because they have not converted yet is a false negative.
Waiting until labels mature means throwing away the young traffic — with
a 3-day-old snapshot there is no mature row at all. The corrected model
keeps every row and gives each censored row a soft label equal to the
probability that it will convert inside the window, estimated from the
delay distribution and the base conversion rate. The naive model
under-reads fresh traffic by a third (0.092 versus 0.132); the corrected
model tracks it (0.142).

## Why this belongs in the mission

The mission measures itself on user value, and user value in a
transactional system is delayed by design. Any dashboard reading of
"fresh traffic converts less" is exactly the naive artifact this stage
isolates: the bias is in the labels, not the users, and every
downstream decision — retraining cadence, budget pacing, LTV — inherits
it unless the delay is modeled.

## The fix and its trade

The fix is a soft label instead of a longer wait: keep every row and give
each in-flight row a label equal to the probability that it converts
inside the window, estimated from the measured delay distribution and the
base conversion rate. The executed read prices the repair — the naive
model under-reads fresh traffic by a third (0.092 against a true 0.132)
while the corrected model tracks it (0.142) on the same young snapshot,
and the conversion AUC moves from 0.666 to 0.672.

The trade is that the correction is only as good as the two numbers it is
built from. The delay distribution and the base rate both drift as the
product changes the funnel, so the estimator is a standing artifact with a
re-check, not a one-time constant — a stale delay estimate turns the soft
label back into a wrong hard label in new clothes. The alternative,
waiting for maturity, is not a trade but a dead end: on a 3-day-old
snapshot the mature set is empty by definition, so "wait for labels" means
"do not train on the traffic you want to serve".

## Who owns the loop

- **The label pipeline team** owns the delay-distribution estimator, the
  attribution window, and the base rate — the two inputs the soft label
  multiplies. When the funnel changes (a new checkout step, a new market),
  the re-estimation is this team's job, and it owns the alert when the
  in-flight share of a young snapshot crosses the bound the estimator
  assumes.
- **The model team** owns the soft-label training and the fresh-traffic
  read: the corrected model's score on young rows is the acceptance test,
  not the offline AUC alone.
- **The monitoring team** owns the under-read dashboard. The naive
  artifact looks exactly like a launch dip or a real engagement decline
  (stage 47's drift lens), so the monitoring read has to separate "labels
  are censored" from "users changed" before anyone acts on the number.

## Evidence boundary

The executed synthetic read over declared delay and snapshot
distributions (illustrative, deterministic). It demonstrates the
false-negative bias and the soft-label correction; real systems need the
measured delay distribution per funnel step, the attribution window, and
validation that the correction's base rate stays honest as traffic
changes.

## Check your mental model

Answer each before opening it.

**1. Why does "just wait for mature labels" fail on a young snapshot?**

<details>
<summary>Answer</summary>

Because maturity is a property of age, and a young snapshot has no old
rows: the mature set is empty by definition, so waiting means not
training on the traffic the system actually wants to serve. The trade is
not between correct and fresh labels — it is between starving on correct
labels and correcting fresh ones.

</details>

**2. What does the soft label estimate, and why is it a probability?**

<details>
<summary>Answer</summary>

It estimates the chance that a row still in flight converts before the
window closes, from the delay distribution and the base rate. It is a
probability, so the loss uses it as a target in expectation — a censored
row contributes w times the positive loss and 1 minus w times the
negative loss — which is why the correction recovers the scale that a
hard negative label destroys.

</details>

## Next

The window itself is a knob: [a one-day window halves the auc, a
30-day window starves the set](when-the-window-is-too-short/) — the
executed read: 0.462 at day 1, peaking at 0.705 near day 7.

Retraining cadence does not fix the bias: [the freshest rows carry the
most false negatives](when-freshness-fights-correctness/) — the executed
read: corrected 0.733 versus naive 0.712 on the same young snapshot.
