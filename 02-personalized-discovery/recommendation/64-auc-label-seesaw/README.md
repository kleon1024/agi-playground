---
status: verified
level: applied
base: scratch
label: AUC-label seesaw
verified: 2026-08-07
---

# Two objectives moved in opposite directions. What do you ship?

**Question:** your shared trunk predicts click and buy from the same
embeddings. You train three variants: one lifts click AUC, another lifts
buy AUC, none wins both. The team splits — the click people want theirs,
the buy people want theirs. What do you do?

**Before this:** [stage 04 — fine-rank](../../shared/04-fine-rank/) for the
shared trunk both objectives read from, and [stage 61 — multi-task
conflict](../61-multi-task-conflict/) for why an abundant task shapes the
trunk these variants build on.

## The seesaw is a trade, not a bug

In multi-task recommendation this exact fight has a name. The PLE paper,
describing Tencent's production recommendation system, calls it the seesaw
(跷跷板): improving one objective's AUC measurably costs another's (Tang
et al., RecSys 2020, DOI 10.1145/3383313.3412236). It is not something
you fix by wishing. One trunk, one loss: the gradient is a compromise, and
when two objectives pull the shared representation in different
directions, neither gets a specialist's fit. The question is never "can we
have both" — it is "which position on the trade are we choosing, and who
decides?"

## The trade, executed

The run ([record](runs/2026-08-07-auc-label-seesaw.md)) trains three
variants on one cohort (762 head / 359 tail click positives, 136 buy
positives in 2,560 rows):

| model | click AUC | buy AUC |
|---|---:|---:|
| naive shared bottom | 0.726 | 0.716 |
| slice-weighted | 0.723 | 0.781 |
| gated (MMoE-lite) | 0.725 | 0.653 |

No variant wins both. Slice weighting buys the buy task (+0.065) and
leaves click flat; gating holds click and gives up the buy task (-0.063).
Read the columns as the seesaw: each row is a different position on the
trade. The rest of this chapter is how you pick a row.

## Decide by contract, not by debate

The reason the meeting ends in a fight is that the objectives were never
ranked. A seesaw is decidable if — before training — you declare the
decision contract: which objective is the primary metric the model is
being improved for, and which are guardrails that may not regress past a
stated threshold. Apply that to the same three rows:

- **Buy primary, click guardrail (click >= 0.720):** slice-weighted
  ships — buy 0.716 to 0.781, and click 0.723 clears the guardrail.
- **Click primary, buy guardrail (buy >= 0.700):** gated is blocked (buy
  0.653), and slice-weighted regresses the primary by 0.003 — the naive
  trunk is the incumbent that ships.

Same three rows, two contracts, two different answers. The numbers did
not change; the objective did. That is the point: a seesaw read after
training can be argued either way, so the contract has to exist before
the run. When teams cannot agree post-hoc, it is usually because nobody
wrote the objective down — the failure is upstream of the model, in the
objective definition, not in the AUCs.

## Before you celebrate a flat delta

Eval rigor matters here, because the aggregate can hide the trade. The
audit ([record](runs/2026-08-07-seesaw-audit.md)) stratifies the same
cohort by slice and task:

| model | head click | tail click | head buy | tail buy |
|---|---:|---:|---:|---:|
| naive | 0.644 | 0.662 | 0.710 | 0.698 |
| slice-weighted | 0.630 | 0.706 | 0.778 | 0.782 |

The click delta that read "flat" (-0.003) is actually the head slice
paying (0.644 to 0.630) and the tail slice gaining (0.662 to 0.706). An
objective-level "no change" can still be a reallocation underneath. So
the eval read is per-objective deltas with intervals, and per-slice
within an objective — never the aggregate alone.

## Solving it: the frontier is the deliverable

The actual fix is not a miracle architecture; it is a dial you sweep, a
frontier you read, and a position someone decides:

- **The weight dial.** Raise the buy task's loss weight and each step is a
  new point on the frontier. The detour measures it: the first steps buy
  the tail cheaply, then the frontier saturates
  ([when-the-slice-trades](when-the-slice-trades/)). Where you sit on the
  saturated frontier is a product decision — which experience is worth
  what — not a model metric.
- **Structure is the scaling answer, not the default.** When one weight
  cannot express the preference because the tasks need different
  expertise, the architecture changes — MMoE (Ma et al., KDD 2018) and
  PLE route tasks through different experts. But a gate is not automatic:
  on this cohort the gated variant lost to the explicit weight (buy 0.653
  vs 0.781), and the diagnostic is the learned gate weights — if they
  collapse toward one expert, the gate is a shared trunk with extra
  parameters.
- **Gradient surgery is tempting and, here, neutral.** The gradients
  conflict in 43 of 60 epochs, yet PCGrad changes nothing: the sparse
  task's bottleneck is gradient amplitude, not direction
  ([when-the-gradients-conflict](when-the-gradients-conflict/)). Start
  with the explicit weight; reach for surgery only with the conflict
  diagnostic in hand.

## Who owns the loop

- **Product owns the frontier position.** Which objective is primary, and
  where on the trade the system should sit, is an experience and business
  decision. The weight sweep's saturation point goes in front of product,
  not model.
- **Evaluation owns the gate.** Per-objective deltas with intervals,
  guardrail thresholds, and the per-slice read. A declared guardrail that
  regressed blocks the ship, whoever likes the primary.
- **The model team owns the structure and the dial.** It builds the
  variants and sweeps the weights; it does not decide the preference.

When the ownership is implicit, the meeting is a debate: the aggregate
looks flat, nobody owns the tail or the guardrails, and the model that
ships is whichever team argued loudest.

## What this chapter does not prove

The numbers come from an executed synthetic cohort (2,560 train rows,
declared slice and task rates, single seed). The decision rule is
demonstrated on those numbers, not fitted to them. In production the same
read runs on real traffic with a contract declared before training and
per-objective intervals — and the calibration axis (whether the score is
a probability, not whether it ranks well) is a separate contract,
measured in [when-the-second-model-costs](when-the-second-model-costs/).

## Check your mental model

Answer each before opening it.

**1. Why does the same table ship different models under two contracts?**

<details>
<summary>Answer</summary>

Because the contract is the decision and the table is only evidence. The
primary metric and the guardrail thresholds turn "some objectives went
up, some went down" into a pass/fail rule; without them, the same numbers
can be argued in either direction, which is exactly the meeting that
never ends.

</details>

**2. Why is gating not the automatic answer to a seesaw?**

<details>
<summary>Answer</summary>

A gate (MMoE/PLE-style) only pays when the tasks disagree about which
expertise they need. On this cohort the gated variant's buy AUC (0.653)
lost to explicit slice weighting (0.781). The learned gate weights are
the diagnostic; the weight dial is the first fix to try, not the
architecture.

</details>

## Next

Return to [stage 61](../61-multi-task-conflict/), or try the three
detours: [the weight frontier](when-the-slice-trades/), [the
gradient-surgery promise](when-the-gradients-conflict/), and the
[separate calibration axis](when-the-second-model-costs/). The same
decision needs numbers that can actually decide: [stage 65 — sparse
labels](../65-sparse-labels/) shows what happens when an objective's
slice has so few positives that its interval spans chance.
