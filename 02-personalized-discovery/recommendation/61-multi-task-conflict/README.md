---
status: verified
level: applied
base: scratch
label: Multi-task conflict
verified: 2026-08-07
---

# The abundant task shapes the shared trunk

**Question:** stage 04 trained several heads off one shared trunk and left
the loss unweighted. This stage asks what happens when the tasks are
drastically different in prevalence — clicks at ~10%, purchases at ~1% —
and answers: the click loss pulls the trunk far harder, so the sparse
task's representation is never shaped by its own signal.

**Before this:** [stage 04 — fine-rank](../../shared/04-fine-rank/) for the
trunk this stage balances.

## The three trunks, executed

The run ([record](runs/2026-08-07-multi-task-conflict.md)) trains a naive
shared bottom, a gradient-balanced variant, and a gated (MMoE-lite) trunk:

| model | CTR AUC | buy AUC |
|---|---:|---:|
| naive shared bottom | 0.582 | 0.461 |
| gradient-balanced | 0.590 | 0.660 |
| gated (MMoE-lite) | 0.608 | 0.564 |

Purchase positives in train: 31 of 2,000. Final gradient norms: CTR 0.484
vs buy 0.076.

## The mechanism, named

With a 10% click rate and a 1% purchase rate, the shared trunk's gradient
is almost entirely click gradient (98.9% in the companion read), so the
representation is built for clicks and the purchase head reads a trunk
that was never shaped by purchases. Balancing the purchase loss rescues
the sparse task outright (buy AUC 0.461 to 0.660); gating improves on the
naive trunk without a hand-tuned weight, landing between the two here.
Gating is the structural answer that scales when the conflict is not one
weight — but it only pays when the tasks actually disagree about which
expertise they need.

## Why this belongs in the mission

The fine-rank trunk is the mission's shared model, and its heads feed every
downstream product of probabilities. A sparse task silently starved inside
the shared trunk is the same failure as stage 56's population bias, one
level down: the abundant task is the "wrong population" for the sparse
one's representation.

## The fix and its trade

The fix is to give the sparse task a vote inside the shared trunk, with
two levers of increasing structural commitment. Gradient balancing
reweights the sparse task's loss — the executed read moves buy AUC from
0.461 to 0.660 on a trunk where the click task's final gradient norm is
0.484 against the buy task's 0.076. Gating (MMoE-lite) lands at buy AUC
0.564 without a hand-tuned weight, improving on the naive trunk without
the tuning cost.

The trade, named: balancing is a hand-tuned weight that must be re-tuned
whenever the task mix moves, and gating pays in structure — extra
parameters and serving cost that only earn their keep when the tasks
disagree about which expertise they need, which is exactly the collapsed
gate in the detour. The cheapest form of the fix is not a fix at all but
a diagnostic: log the per-task trunk gradient norms during training,
because a share as imbalanced as 98.9%-to-1.1% is visible before any
evaluation. The naive trunk looks like a model problem and is a sample
and objective problem one level down.

## Who owns the loop

- **The model team** owns the trunk, the per-task loss weights, and the
  learned gate audit — the gate weights are logged and checked per slice
  before gating is trusted.
- **The evaluation team** owns the per-task validation balance: the
  acceptance read is buy AUC beside CTR AUC, never CTR AUC alone.
- **The serving team** owns the cost of the chosen architecture — gating
  is a serving decision as much as a modeling one, and a collapsed gate
  pays for parameters that do nothing.
- **The monitoring team** owns the per-task trunk gradient norms during
  training, the number that says when the conflict has drifted back and a
  weight or a gate needs re-tuning.

## Evidence boundary

The executed synthetic read over 2,000 rows with declared task rates
(illustrative, deterministic). It demonstrates the balance and gating
effects on a single seed; real systems must tune per-task weights on
validation and audit the learned gate weights before committing to gating.

## Check your mental model

Answer each before opening it.

**1. Why does the sparse task lose inside a shared trunk?**

<details>
<summary>Answer</summary>

Because the trunk's gradient is a weighted sum of task gradients, and the
abundant task contributes almost all of it. The representation follows the
dominant gradient; the sparse head then reads a trunk built for someone
else.

</details>

**2. When does gating not pay?**

<details>
<summary>Answer</summary>

When both tasks want the same representation. The gate collapses to a
single expert and the architecture becomes a shared bottom with extra
parameters and serving cost — the diagnostic is the learned gate weights.

</details>

## Next

The two failure faces: [the dominant task owns 98.9% of the trunk
gradient](when-the-dominant-task-wins/), and [gating collapses when tasks
agree](when-gating-does-not-help/).
