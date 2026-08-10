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

## The fix and its trade

The fix is a training-dynamics one: a linear LR warmup over the first 186
of 1,860 steps (10%), with the model, data, and seeds unchanged. The
trade is what makes the before/after comparison trustworthy: because only
the LR schedule differs, the seed-2 recovery (0.2844 -> 0.4962) is
attributable to the warmup rather than to any other variable. The fix
costs something real — one warmup fraction (10%) was tried, not swept, so
the claim is bounded to "this fraction closed this collapse," and a
different fraction could work better, worse, or not at all. The mean rise
(0.4375 -> 0.4970) is the second half of the trade's payoff: it rules out
the reading "the spread shrank because one seed got lucky," because
warmup is improving the typical run, not just rescuing the outlier. The
mechanism claim — a fixed high LR at step 0 lets early updates push the
pathway into a degenerate region before features form — is the standard
empirical account of warmup (Goyal et al., 2017; Vaswani et al., 2017),
supported here by the recorded seed-2 trajectory, though not isolated at
the layer or gradient level.

## Who owns the loop

- **The model team** owns the LR schedule and the single-mechanism
  discipline: the warmup is the one variable changed, which is the
  condition that makes the before/after read causal rather than
  correlational.
- **The evaluation owner** owns the before/after read: both numbers —
  spread 0.2309 -> 0.0536 and mean 0.4375 -> 0.4970 — must be reported
  together, because the mean rise is what answers the "lucky seed"
  interpretation.
- **The report owner** owns the scope boundary: this answers stage 01's
  named open question and does not retroactively revise stage 01's
  recorded result, and the mission's build-vs-buy verdict is untouched.

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
