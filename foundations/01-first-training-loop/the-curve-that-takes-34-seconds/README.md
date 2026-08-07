---
status: verified
level: foundation
base: scratch
label: The curve that takes 34 seconds
verified: 2026-08-06
---

# The descent and the overfitting are the same curve

**Question:** [the first training loop](../) trains a 10.75M GPT on Tiny
Shakespeare in 34 seconds. The recorded run holds the train/val loss at
every checkpoint; this chapter reads that curve and asks what it actually
says about the loop.

**Before this:** [the first training loop](../) — you need the loop running
before the curve it produces means anything.

## The curve, read

The run ([record](runs/2026-08-06-curve-read.md)) reads the recorded
checkpoints:

| iter | train | val | gap |
|---:|---:|---:|---:|
| 0 | 4.327 | 4.327 | +0.001 |
| 500 | 2.037 | 2.095 | +0.058 |
| 1000 | 1.482 | 1.664 | +0.182 |
| 1500 | 1.327 | 1.570 | +0.243 |
| 2000 | 1.275 | 1.538 | +0.263 |

## Two readings

**The loop learns fast, and that speed is the first thing to check.** Val
loss falls from 4.327 to 1.538 in 2000 iterations and 34.2 seconds — the
curve is the loop's health check. A loop whose loss does not fall this way
is broken in some mechanical way (wrong mask, wrong loss, learning rate
too high), and the recorded descent is the shape to compare against.

**The train/val gap grows monotonically: the toy memorizes its training
set by the end.** The gap starts at +0.001 and ends at +0.263 — training
keeps improving while validation stalls, the textbook signature of
overfitting on 1.1MB of text. It is a diagnostic, not a failure: the
chapter's job is the loop, not generalization, and the gap is where the
later curriculum (data scale, regularization, evaluation) begins.

## Evidence boundary

The recorded 2000-iteration run (one seed, one architecture, one 1.1MB
corpus). It reads the recorded curve; it does not re-train and does not
claim the gap would look the same at another scale.

## Check your mental model

Answer each before opening it.

**1. The val loss keeps falling to the end. Why does the chapter call the
later part of the curve overfitting?**

<details>
<summary>Answer</summary>

Because overfitting is about the *gap*, not the val number itself. Train
loss falls faster than val from around iteration 500, and the gap widens
from +0.001 to +0.263. The val number still improves — 1.664 to 1.538 —
but each later step buys less real generalization and more memorization,
which is what the widening gap measures.

</details>

**2. What would a broken loop look like on this curve?**

<details>
<summary>Answer</summary>

A flat or rising loss, or a descent much slower than the recorded one.
Because the recorded descent is the loop's expected health shape, a
deviation is a mechanical bug — wrong loss reduction, an attention mask
leaking future tokens, or a learning rate that diverges — not a tuning
question. The curve is the first diagnostic a training loop gives you.

</details>

## Next

Back to [the first training loop](../), or to
[what are you actually training](../../../01-language-model/02-pretrain/)
where this same loop runs at 3B tokens instead of 1.1MB.
