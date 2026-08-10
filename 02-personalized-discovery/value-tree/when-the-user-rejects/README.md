---
status: verified
level: applied
base: scratch
label: When the user rejects
verified: 2026-08-07
---

# The dislike that flips the weight

**Question:** [stage 05's value tree](../) combines user value and revenue
into one score. This chapter reads the executed rejection run and asks
what an explicit negative does to the trade.

**Before this:** [stage 05 — value tree](../) and its executed combination.

## The rejection, executed

The run ([record](runs/2026-08-07-reject-read.md)) prices three items and
then applies one explicit dislike:

| item | before | after rejection |
|---|---|---:|
| x | score 0.65 | -0.15 |
| y | score 0.15 | 0.15 |
| z | score 0.40 | 0.40 |

## Two readings

**One explicit negative rewrites the trade.** Item x had the highest
combined score — user value 0.8 against revenue 0.3 — and the rejection
drops its user value to zero, leaving the revenue term to push the score
below zero. The item falls from the top of the slate to below the fold on
a single signal. The value tree is exactly as responsive as its input
signals.

**The value tree is only as current as its signals.** A rejection is rare
but strong; a missing rejection is the default, which is why the tree
learns most values from the weaker implicit signals of stage 00. The run
shows the mechanism at its strongest — the point of the tree is that user
value and revenue are priced together, and the dislike demonstrates that
user value can be revoked, not just accumulated.

## The fix and its trade

The fix is to treat explicit negatives as first-class value signals: user
value is revocable, not just accumulable, and the tree must price the
revocation. The executed run shows the mechanism at its strongest: item x
falls from the top of the slate (0.65) to below the fold (-0.15) on one
dislike — its user value (0.8) zeroes out and the revenue term (0.3) is
all that remains — while y and z, untouched, keep their scores. One
signal rewrites the trade, which is exactly the responsiveness a value
tree is supposed to have.

The trade, named: explicit signals are rare but strong, and their absence
is the default — the tree learns most user values from the weaker implicit
signals of stage 00, so responsiveness is only as good as signal
freshness. The repair is a feedback pipeline that converts a dislike into
an updated user-value component with bounded latency; the cost is the
pipeline and the noise it must survive, because a false-negative
rejection is as consequential as a real one. The tree's job is to make
the trade visible per item, and the executed flip is the number the
product decision is read from.

## Who owns the loop

- **The product team** owns the feedback contract — what counts as a
  rejection and how fast it must change the value is a product decision.
- **The model team** owns the signal pipeline that turns explicit feedback
  into updated user-value components within the agreed latency.
- **The evaluation team** owns the flip read: a before-and-after slate
  comparison per feedback type, so the tree's responsiveness is measured,
  not assumed.

## Evidence boundary

The executed hand-built slate (illustrative, deterministic). It
demonstrates the flip; real rejection signals are sparse and noisy, which
is why they are blended with exposure-based estimates rather than taken
at face value.

## Check your mental model

Answer each before opening it.

**1. Why does x go below y and z after the rejection?**

<details>
<summary>Answer</summary>

Because the rejection zeroes the user-value term and leaves the revenue
term to act alone. x's score becomes -0.15 — revenue it no longer earns
its keep for. y and z are unchanged because their user value was never
revoked. The score is a combination, so removing one component changes
the ordering even when the other components stay fixed.

</details>

**2. Why is the rejection stronger than the implicit signals?**

<details>
<summary>Answer</summary>

Because it is explicit — the user acted against the item, not just failed
to engage. A non-click can mean "not interested" or "did not see it"; a
rejection says the item was seen and refused. That is why it can zero the
user value in one step where implicit signals need many exposures to
converge. The tree weights the signal by how much the user committed to
producing it.

</details>

## Next

Back to [stage 05](../), or to
[the weight that is the strategy](../when-the-weight-moves/) for the
revenue side of the same combination.
