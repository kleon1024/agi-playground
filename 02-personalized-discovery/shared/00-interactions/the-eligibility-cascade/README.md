---
status: verified
level: applied
base: scratch
label: The eligibility cascade
verified: 2026-08-06
---

# The filter that catches users it did not aim at

**Question:** [stage 00's eligibility filter](../) drops users and items
below interaction thresholds. This chapter reads the recorded MovieLens run
and asks what the *iterative* part of the filter actually does.

**Before this:** [stage 00's split](../) and its recorded run.

## The cascade, read

The run ([record](runs/2026-08-06-cascade-read.md)) reads the recorded
numbers:

| fact | value |
|---|---|
| rows dropped | 10,562, all for item sparsity |
| sparse movies | 6,074 of 9,724 (under 5 ratings) |
| users the cascade caught | 8, including user 175 (24 -> 12), 598 (21 -> 16), 578 (27 -> 17) |

## Two readings

**Eligibility is per item AND per user, and the two interact.** Dropping a
sparse item can push a user below their own threshold, which can push
another item below its own. The users above are the proof: their ratings
were fine, but removing their sparse items removed the support that kept
them eligible. A filter that passes once misses this; the loop exists
because the cascade is real.

**The cascade is a property of the data, not a bug in the filter.** 8 users
of 610 fell below the floor only after item drops — a small but real
fraction, and exactly the kind of silent edge a one-pass implementation
would ship. The recorded run names three of them so the mechanism is a
concrete row, not an abstraction.

## Evidence boundary

The recorded MovieLens split run (one dataset, default thresholds). It
reads the recorded numbers; it does not re-run the filter and does not
extend the cascade to other thresholds, where the count would move.

## Check your mental model

Answer each before opening it.

**1. Why does the filter need to loop at all?**

<details>
<summary>Answer</summary>

Because the two thresholds interact. Dropping a sparse item can push a user
below the user threshold; dropping that user can push another item below
the item threshold. A single pass fixes the immediate offenders and leaves
the second-order ones, which is why the run records users like 175 (24 ->
12) that only fell after their sparse movies were gone.

</details>

**2. Why are these users evidence and not noise?**

<details>
<summary>Answer</summary>

Because they were eligible before any filtering — user 175 had 24 ratings,
above the floor — and became ineligible only through the cascade. That is
the difference between "the filter works" and "the filter works on the
first pass": the drop is attributable to the item interaction, not to the
user's own data, and a one-pass implementation would silently lose them.

</details>

## Next

Back to [stage 00](../), or to
[the split that leaks](../when-the-split-leaks/) which reads the same run's
leakage comparison.
