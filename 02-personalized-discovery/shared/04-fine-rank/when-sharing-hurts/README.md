---
status: verified
level: applied
base: none
label: When sharing hurts
verified: 2026-08-06
---

# When does the shared model hurt an objective?

**Question:** [stage 04](../) trains one model with a shared trunk and a
head per objective. Sharing is a bet: the trunk learns what the tasks have
in common, and pays when one task's gradient fights another's. This chapter
measures the transfer directly — per objective, shared versus trained alone.

**Before this:** [stage 04's fine-rank](../), including its recorded
weighting comparison.

## The transfer grid, measured

The run ([record](runs/2026-08-06-transfer-grid.md)) trains the shared model
and each single-task variant on the same data:

| task | naive transfer | balanced transfer |
|---|---:|---:|
| click | -0.037 | +0.001 |
| completion | -0.023 | -0.001 |
| satisfaction | +0.051 | -0.040 |

## Two readings

**Negative transfer is real, per-task, and direction-dependent.** In naive
mode the shared trunk hurts click (-0.037) and completion (-0.023) while
satisfaction gains (+0.051) — the trunk's shared geometry serves one
objective at the others' expense. The dwell objective is excluded from the
reading: its target is continuous seconds and the ranking metric is binary,
so its row is the metric's None, not a result.

**The weighting decides WHICH task pays.** The balanced weighting flips the
pattern: click and completion recover to near zero, satisfaction turns
negative (-0.040). The stage's recorded naive-vs-scale-normalized claim is
exactly this — the shared model's transfer is not a property of the
architecture alone; it is a property of how the tasks' gradients are
weighted, which is the lever the fine-ranker actually tunes.

## Evidence boundary

One seed per cell, 200 synthetic examples, 40 epochs; the directions are the
finding, not the magnitudes. It measures transfer on this toy; it does not
claim the pattern transfers to real multi-task recommenders, and it does
not cover the calibration axis (the stage's recorded run owns that).

## Check your mental model

Answer each before opening it.

**1. Why can a shared trunk help satisfaction while hurting click on the
same data?**

<details>
<summary>Answer</summary>

Because the trunk's hidden geometry is one set of features serving all four
heads. The tasks' gradients pull it in different directions; the head whose
signal is best represented by the shared geometry gains, and the tasks whose
signal is diluted by the competing gradients lose. Negative transfer is the
measurement of that competition, and it is per-task by construction.

</details>

**2. The balanced weighting flips which tasks transfer negatively. What does
that say about the fine-ranker's real knob?**

<details>
<summary>Answer</summary>

That the transfer is not fixed by the architecture — it is set by the loss
weighting, because the weighting controls how much each task's gradient
shapes the shared trunk. The naive mode lets the dwell loss (raw seconds)
dominate, and the balanced mode re-scales it, which re-distributes the
shared geometry. The fine-ranker's product-relevant choice is therefore
the weights, not the model.

</details>

## Next

Back to [stage 04's fine-rank](../), or forward to
[stage 05's value tree](../../05-value-tree/) where the multi-objective
predictions get collapsed into the ranking scalar.
