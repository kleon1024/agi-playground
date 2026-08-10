---
status: verified
level: foundation
base: scratch
label: The flips that separate the optimizers
verified: 2026-08-06
---

# Fewer flips is what makes fewer steps possible

**Question:** [the optimization chapter](../) races SGD, momentum, and Adam
on one ill-conditioned bowl. This chapter reads the recorded run and asks
what the step counts and the sign-flip counts have to do with each other.

**Before this:** [the optimization chapter](../) and its recorded
optimizer comparison.

## The comparison, read

The run ([record](runs/2026-08-06-flip-read.md)) reads the recorded JSON:

| optimizer | steps to converge | steep-axis flips | flips per step |
|---|---:|---:|---:|
| SGD | 343 | 341 | 0.99 |
| momentum | 138 | 47 | 0.34 |
| Adam | 82 | 4 | 0.05 |

## Two readings

**The flip count is the direct measure of oscillation across the steep
axis.** The bowl is A=100, B=1 — one direction curves 100x harder than the
other. SGD, with no memory, zigzags across the steep direction, flipping
the sign of its update on 341 of 343 steps. Momentum averages past steps,
so the zigzag partially cancels (47 flips in 138 steps); Adam's per-
parameter scaling nearly removes it (4 in 82).

**Fewer flips is what makes fewer steps possible — the two numbers move
together.** 343, 138, 82 steps; 0.99, 0.34, 0.05 flips per step. The
optimizer that stops oscillating converges first, which is the mechanism
behind the chapter's headline: the difference between "an update rule" and
"a mechanism" is exactly the flip count.

## The fix and its trade

The failure the flip count names is oscillation: each flip is a step spent
correcting the previous step instead of progressing, and 341 of 343 steps
spent correcting is a run that rings instead of walks. The fix is the
update rule's memory. Momentum averages past gradients, so the alternating
signs partially cancel — 341 flips become 47 — and the cancellation is the
damping; Adam goes further and normalizes each parameter's step by its own
gradient history, which removes the overshoot that causes the alternation
in the first place (4 flips). The trade is measured by what each rule
carries: momentum adds a velocity per parameter and a coefficient (mu)
whose setting trades escape speed against settling time, and Adam adds two
per-parameter statistics plus two more coefficients (beta1, beta2) — the
memory that removes the flips is state the training loop has to store and
tune. The [plateau detour](../when-the-training-plateaus/) measures the
same trade from the other side: on a flat minimum it is the memory that
escapes the stall, and a mu turned too high re-creates a different stall
as ringing.

## Who owns the loop

The flip count is only useful if someone owns the failure it names, and
each owner is tied to one reading of the table:

- **The optimizer and algorithm team** owns the update rule and the
  flip-damping: the mu coefficient and the beta pair are the knobs that
  turn 341 flips into 47 and then 4, and a run that rings instead of
  walks is this team's failure to tune, not the surface's.
- **The training-infra team** owns the conditioning: the A=100/B=1 bowl
  is a statement about the problem's curvature, and feature scaling or
  preconditioning that lowers the condition number changes what the flip
  count is even measuring before the optimizer runs.
- **The research and evaluation team** owns the mechanism-not-leaderboard
  read: the step counts (343, 138, 82) are the outcomes and the flips per
  step (0.99, 0.34, 0.05) are the mechanism, and a comparison that
  reports only the former cannot say why one rule won.

When ownership is implicit, the optimizer team tunes mu against a bowl
the infra team never conditioned, and the eval team reports a ranking
with no mechanism — the same oscillation failure from three sides.

## Evidence boundary

The recorded optimizer comparison (one bowl, one start point, one loss
tolerance; deterministic — re-running reproduces the identical JSON). It
reads that artifact; it does not extend the ranking to real transformer
loss surfaces, where the chapter's own discussion of the condition number
is the boundary.

## Check your mental model

Answer each before opening it.

**1. Why does SGD flip the sign of its update on nearly every step?**

<details>
<summary>Answer</summary>

Because it has no memory. On the steep axis (A=100), a plain gradient step
overshoots past the minimum of that direction, and the next step has to
correct back across it — an oscillation that repeats every step. Momentum
averages the previous steps, so the corrections partially cancel; Adam
scales each parameter by its own history, shrinking the overshoot itself.

</details>

**2. Could an optimizer be fast without having a low flip count?**

<details>
<summary>Answer</summary>

Not on an ill-conditioned surface. Oscillation across the steep axis is
what wastes steps — each flip is a step spent correcting the previous one
instead of progressing. A low step count and a low flip count are the same
measurement on this bowl, which is why the flip count is the mechanistic
explanation and the step count is the outcome.

</details>

## Next

Back to [the optimization chapter](../), or to
[your first training loop](../../01-first-training-loop/) which uses the
default optimizer this chapter explains.
