---
status: verified
level: applied
base: scratch
label: The collapse that warmup closed
verified: 2026-08-06
---

# The seed-2 outlier, closed by a training-dynamics fix

**Question:** [stage 06's warmup stability](../) retrained the vision
pathway with a linear LR warmup. This chapter reads the recorded run and
asks what the warmup actually changed.

**Before this:** [stage 06's warmup stability](../) and its recorded JSON.

## The before/after, read

The run ([record](runs/2026-08-06-warmup-read.md)) reads the recorded
numbers:

| | stage 01 | with warmup |
|---|---:|---:|
| eval mean | 0.4375 | 0.4970 |
| eval spread | 0.2309 | 0.0536 |
| per-seed | 0.5128, 0.5153, **0.2844** | 0.4707, 0.5242, 0.4962 |

Warmup: linear 0 -> 3e-3 over the first 186 of 1,860 steps (10%), then held
constant.

## Two readings

**The collapse was the seed-2 outlier, and warmup closed it.** Stage 01's
spread (0.2309) was one bad seed (0.2844) against two good ones. With
warmup, seed 2 lands at 0.4962 — the collapse is gone, and the spread
tightens to 0.0536, a 4.3x reduction. The fix is a training-dynamics one:
the model, data, and seeds are unchanged, only the LR schedule differs.

**Warmup did not just remove the outlier; it raised the mean.** Eval
exact-match rises 0.4375 -> 0.4970, so the fix is not "the collapse was
one seed and warmup hid it" — the warmup's gentler start also improves the
typical run. The mechanism: a fixed high LR at step 0 lets the vision
pathway diverge before it has learned anything; a warmup keeps the early
updates small enough to survive.

## Evidence boundary

The recorded warmup run (three seeds, 30 epochs, one architecture, one
schedule; text-only not re-run because the collapse is vision-specific).
It reads that artifact; it does not re-train.

## Check your mental model

Answer each before opening it.

**1. Why does a warmup fix a collapse that a lower LR might not?**

<details>
<summary>Answer</summary>

Because the collapse happens at the very start. At step 0 with a fixed
3e-3 LR, the vision pathway's early updates are large enough to push it
off into a degenerate region before it has learned any useful feature. A
warmup keeps the first 186 steps tiny, so the pathway survives the
initialization phase; the recorded seed-2 recovery (0.2844 -> 0.4962) is
that survival made visible.

</details>

**2. What does the mean rise add beyond the spread reduction?**

<details>
<summary>Answer</summary>

It rules out the reading "the spread shrank because one seed got lucky."
The mean rises from 0.4375 to 0.4970 across all three seeds, so warmup is
not just closing the outlier — it is improving the typical run too. The
fix is robust to the interpretation question, which is why both numbers
(mean and spread) are reported.

</details>

## Next

Back to [stage 06](../), or to
[what the warmup changed, and what it did not](../when-warmup-closed-the-collapse/)
which reads the same run's scope.
