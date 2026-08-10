---
status: verified
level: applied
base: scratch
label: When the dominant task wins
verified: 2026-08-07
---

# The trunk built for clicks

**Question:** [stage 61](../) balances a shared trunk. This chapter makes
the imbalance concrete: at a 10% click rate and a 0.1% purchase rate, the
click task owns nearly all of the trunk gradient.

**Before this:** [stage 61 — multi-task conflict](../).

## The gradient split, executed

The run ([record](runs/2026-08-07-dominant-task-wins.md)) reads the trunk
gradient share:

| task | trunk gradient share |
|---|---:|
| click | 98.9% |
| purchase | 1.1% |

## The reading

With a 10% click rate and a 0.1% purchase rate, nearly all of the trunk
gradient comes from the click task, so the shared representation is built
for clicks. The purchase head then reads a representation that was never
shaped by purchases — which is stage 61's buy AUC 0.461 in a single
number. Reweighting the task loss or gating the experts is what gives the
sparse task a say; the gradient share is the diagnostic that tells you
when to bother.

## The fix and its trade

The fix is to rebalance the trunk gradient — reweight the task loss or
gate the experts — and the executed read is the diagnostic that says when
to bother: at a 10% click rate and a 0.1% purchase rate, the click task
owns 98.9% of the trunk gradient and the purchase task 1.1%. A share that
imbalanced means the representation is built for clicks, and the purchase
head reads features that never encoded purchase signal — stage 61's buy
AUC of 0.461 in a single number.

The trade, named: rebalancing transfers gradient from the dominant task to
the sparse one, so it trades a little click accuracy for purchase
accuracy, and the weights have to be tuned on validation, not guessed —
over-weight the sparse task and the trunk stops serving the abundant one.
The cheapest form of the fix is the diagnostic itself: per-task trunk
gradient norms logged during training make the imbalance visible before
any model is judged, and say which task needs a weight before the
evaluation, not after.

## Who owns the loop

- **The model team** owns the per-task gradient-norm logging and the
  reweight — the share read is a training-time artifact, not an
  evaluation-time surprise.
- **The evaluation team** owns the per-task validation balance and the
  guardrail that a reweighted trunk must not collapse the dominant task
  below its bound.
- **The monitoring team** owns the gradient-share read on every run, so a
  distributional shift that re-imbalances the trunk is caught at training
  time, not in a production metric dip.

## Evidence boundary

The executed read over declared task rates (illustrative, deterministic).
It demonstrates the imbalance; real systems must log per-task trunk
gradient norms during training and rebalance when one task's share
crosses a chosen bound.

## Check your mental model

Answer each before opening it.

**1. Why is 1.1% of the gradient a death sentence for the sparse task?**

<details>
<summary>Answer</summary>

Because the trunk updates toward the click gradient almost every step, so
the representation optimizes clicks and the purchase head has to work with
features that never encoded purchase signal.

</details>

**2. What is the cheapest diagnostic?**

<details>
<summary>Answer</summary>

Per-task trunk gradient norms logged during training. A share this
imbalanced is visible before any evaluation, and it says which task needs
a loss weight before the models are judged.

</details>

## Next

Back to [stage 61](../). The other face: [gating collapses when both tasks
want the same representation](../when-gating-does-not-help/).
