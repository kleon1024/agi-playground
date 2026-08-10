---
status: verified
level: applied
base: scratch
label: When the absence is a signal
verified: 2026-08-07
---

# The absence is a signal

**Question:** [stage 00's interaction model](../) counts clicks. This
chapter reads the executed exposure log and asks what a zero means —
there are two kinds, and they carry opposite information.

**Before this:** [stage 00 — interactions](../) and its executed log
model.

## The two zeros, executed

The run ([record](runs/2026-08-07-absence-read.md)) reads an exposure log
with four items:

| item | exposures | clicks | reading |
|---|---:|---:|---|
| A | 1000 | 120 | ctr 0.120 |
| B | 1000 | 4 | ctr 0.004 |
| C | 1000 | 0 | implicit negative |
| D | 0 | 0 | no signal |

## Two readings

**A zero click after exposure is a real negative.** Item C was shown 1000
times and clicked zero times — the user saw it and chose not to engage.
That is information: the item underperforms its exposure. Item B shows
the contrast, 4 clicks per 1000 views; C sits below even that.

**A zero with zero exposure is silence.** Item D has no clicks because it
was never shown, and treating it like C would be wrong in the opposite
direction — it would reward never-shown items and punish honest
failures. The two zeros must be separated at the log level, because every
downstream stage (recall, ranking, value) inherits whatever the
interaction model did with them.

## The fix and its trade

The fix is to separate the two zeros at the log level before any model sees
the data: a zero click after exposure (item C, 1000 exposures, 0 clicks) is
an implicit negative, and a zero with zero exposure (item D) is silence.
The executed read prices the distinction — C's zero is a measured outcome
of showing the item, D's is a missing row — and every downstream stage
inherits whichever treatment the interaction model chose.

The trade, named: treating the zeros separately costs the log team an
exposure record for every item, shown or not, which is real logging volume
that a click-only log never paid. The alternative — merging the zeros — is
cheaper to record and doubly wrong: shown-and-rejected items become
indistinguishable from never-shown ones, and never-shown items carry a safe
zero that rewards absence, pushing the incentive away from showing anything
at all. The exposure row is the price of learning which items to demote.

## Who owns the loop

- **The logging team** owns the exposure row: an impression, a position,
  and the item, recorded whether or not it was clicked. The separation of
  the two zeros is a log-level decision, not a model-time one.
- **The model team** owns using the implicit negative correctly — C is a
  training signal, D is not a negative and not a positive, and treating D
  as either is a modeling error.
- **The serving team** owns the exposure policy itself: which items get
  shown is what creates C-type rows, and the exploration that creates
  D-type rows is a serving decision with a coverage cost (stage 59's thin
  exploration read).

## Evidence boundary

The executed hand-built exposure log (illustrative, deterministic). It
demonstrates the log-level distinction; real logs add position and
context to decide how much of a non-click is the item versus the slot it
was shown in.

## Check your mental model

Answer each before opening it.

**1. Why is C's zero information and D's zero not?**

<details>
<summary>Answer</summary>

Because C was given a chance to be clicked — 1000 exposures — and failed
it. The absence of a click is a measured outcome of showing the item. D
was never exposed, so there is no outcome at all, only a missing row.
One is a signal about the item; the other is a gap in the data.

</details>

**2. What breaks if the two zeros are merged?**

<details>
<summary>Answer</summary>

Two failures at once. Items that were shown and rejected look identical
to items that were never tried, so the model cannot learn which items to
demote. And because never-shown items carry a safe zero, an item can look
better by simply never appearing — the incentive points away from
showing anything at all.

</details>

## Next

Back to [stage 00](../), or to
[the 99.1% leak](../when-the-split-leaks/) for what the log's splits do to
the same data.
