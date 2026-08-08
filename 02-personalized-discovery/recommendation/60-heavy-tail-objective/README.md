---
status: verified
level: applied
base: scratch
label: Heavy-tail objective
verified: 2026-08-07
---

# The whale owns a fifth of the gradient

**Question:** every earlier stage assumed the label's scale is worth
regressing directly. This stage asks what happens when the label is
transaction value — a heavy tail where a few orders dwarf the rest — and
answers: raw MSE fits the whales, and the fix is a transform or a
decomposition that gives the 99% a vote.

**Before this:** [stage 05 — the value tree](../../shared/05-value-tree/)
for where GMV enters the objective, and [stage 04 — fine-rank](../../shared/04-fine-rank/)
for the multi-task trunk the objective is trained on.

## The three regressions, executed

The run ([record](runs/2026-08-07-heavy-tail-objective.md)) fits GMV with
raw MSE, log(1+GMV), and a decomposed order-probability times conditional
amount:

| method | rel err | whale gradient share |
|---|---:|---:|
| raw MSE | 1.409 | 21.2% |
| log(1+GMV) | 1.045 | 5.2% |
| decomposed | 1.290 | not applicable |

## The mechanism, named

MSE over GMV is dominated by the largest orders: their residuals own a
fifth of the gradient, so the model fits whales and treats the 99% as
noise. The log transform compresses the tail — the same gradient share
drops to a twentieth — at a small error cost. The decomposition splits the
problem into a binary order probability and a conditional amount
regression, landing between the two on pure error but giving each piece its
own interpretation and its own tuning lever. Its payoff is structure, not
the headline number.

## Why this belongs in the mission

The value tree blends engagement, value, and revenue. A heavy-tail label
makes that blend dishonest in one direction: the revenue term quietly
becomes "fit the whales." The transform is the cheapest repair; the
decomposition is the structural one, and the choice between them is a
product decision about whether the tail is signal or noise.

## The fix and its trade

The fix is to change the objective so the common case gets a vote: log
compresses the tail, and the decomposition splits the target into an
order probability and a conditional amount. The executed read prices the
repair — raw MSE lands at a relative error of 1.409 with the whales
owning 21.2% of the gradient; log(1+GMV) drops the error to 1.045 and the
whale share to 5.2%; the decomposed model lands at 1.290 with no single
whale share, because its payoff is structure, not the headline number.

The trade, named: each fix pays in a different currency. The log
transform is the cheapest repair — one line, and the tail stops owning
the fit — but it keeps one opaque regression whose scale is now
harder to interpret. The decomposition pays a little error for two levers
that can be tuned and monitored independently, which the AOV-skews
detour shows is a real operational need, not a nicety. And the deeper
trade is a product decision the loss cannot make for you: whether the
whale rows are signal worth fitting or noise worth compressing, which is
decided per business, not per paper.

## Who owns the loop

- **The model team** owns the objective choice and its holdout
  validation — the transform or decomposition is a modeling contract
  that has to be re-validated on fresh data, not decided once.
- **The product team** owns the whale-is-signal-or-noise decision: the
  tail's treatment changes the served ranking for the 99%, and that is a
  business judgment, not a loss-function default.
- **The monitoring team** owns the top-decile gradient share during
  training — the number that says when the objective has quietly drifted
  back toward fitting whales.
- **The evaluation team** owns the per-method error read on holdout and
  the calibration check that a transformed target still produces honest
  probabilities downstream.

## Evidence boundary

The executed synthetic read over a declared order distribution
(illustrative, deterministic). It demonstrates the gradient and error
effects; real systems must measure the actual GMV tail, decide whether the
whale rows are signal, and validate the chosen objective on a holdout.

## Check your mental model

Answer each before opening it.

**1. Why does raw MSE fit whales, not the median order?**

<details>
<summary>Answer</summary>

Because squared error weights large residuals quadratically. A whale order
ten times the median carries a hundred times the weight, so the fit
spends its capacity on the tail and treats the common case as noise.

</details>

**2. What does the decomposition buy that the log transform does not?**

<details>
<summary>Answer</summary>

Separate levers: the order probability and the conditional amount can be
re-tuned and monitored independently. The log transform compresses the tail
but keeps one opaque regression; the decomposition pays a little error for
interpretability.

</details>

## Next

The tail has a per-cohort face: [a flash sale doubles the rate and halves
the AOV for the same expected value](when-the-aov-skews/), and the whale
itself: [the top 1% of orders own 25.4% of the gradient under raw
MSE](when-the-whale-dominates/).
