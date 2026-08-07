---
status: verified
level: applied
base: scratch
label: AUC-label seesaw
verified: 2026-08-07
---

# The slice that pays for the visible objective

**Question:** stage 04 trained several heads off one shared trunk, and
stage 61 showed the abundant task shapes it. This stage asks the
evaluation question: when the aggregate AUC is flat, which slice and
which task are quietly paying for the objective the model is visibly
optimizing?

**Before this:** [stage 04 — fine-rank](../../shared/04-fine-rank/) for the
shared trunk, [stage 61 — multi-task conflict](../61-multi-task-conflict/)
for the task-balance mechanism this stage's variants build on, and
[stage 05 — the value tree](../../shared/05-value-tree/) for why every
probability the model emits must stay honest.

## The three structures, executed

The run ([record](runs/2026-08-07-auc-label-seesaw.md)) trains a naive
shared bottom, a slice-weighted variant, and a gated (MMoE-lite) trunk on
the same cohort, with click positives split 762 head / 359 tail and buy
positives 136 of 2,560:

| model | click AUC | buy AUC |
|---|---:|---:|
| naive shared bottom | 0.726 | 0.716 |
| slice-weighted | 0.723 | 0.781 |
| gated (MMoE-lite) | 0.725 | 0.653 |

## The mechanism, named

The head slice is denser and higher-signal than the tail, so a naive
shared trunk's gradient is a head gradient: it fits the head's click
signal and the tail slice pays. Slice weighting lifts tail click AUC from
0.662 to 0.706 while head click AUC falls 0.644 to 0.630, and the
aggregate click AUC moves only 0.726 to 0.723 — a number a dashboard calls
flat. The seesaw has a third axis too: the naive click head's calibration
slope is 1.188, so its ranking score is not a probability even where the
order is right. Gating did not win on this cohort (buy AUC 0.653 against
0.781 for the explicit weight): a gate pays only when the tasks disagree
about which expertise they need, which is stage 61's detour
`when-gating-does-not-help` measured. The structure that separates task
expertise — MMoE (Ma et al., KDD 2018) and its layered descendant PLE
(Tang et al., RecSys 2020) — is the scaling answer when the conflict is
not one weight, but it is not automatic.

## How you find it: the stratified AUC matrix, executed

The aggregate hides the seesaw by construction, so the case-finding audit
([record](runs/2026-08-07-seesaw-audit.md)) reads the emitted cohort
envelope and stratifies the AUC matrix by slice and task for the naive and
slice-weighted models, plus the per-decile calibration of the naive click
head:

| model | head click | tail click | head buy | tail buy |
|---|---:|---:|---:|---:|
| naive | 0.644 | 0.662 | 0.710 | 0.698 |
| slice-weighted | 0.630 | 0.706 | 0.778 | 0.782 |

The verdict is AGGREGATE AUC HIDES THE TAIL SLICE TRADE: the aggregate
number hides the reallocation, and ranking on it alone ships a head model
and calls the tail loss noise. The calibration read (slope 1.188,
intercept -0.077) adds the third axis: the same model that looks fine
ranked is broken as a probability source for the value tree. The name for
this trade in the multi-task recommendation literature is the seesaw
(跷跷板) — the term comes from the PLE paper (Tang et al., RecSys 2020,
DOI 10.1145/3383313.3412236), which reports exactly this head-versus-tail
and task-versus-task AUC trade in production multi-task recommendation and
answers it with progressive layered extraction.

## Who owns the loop

The seesaw is a model-structure and evaluation problem, and its handoffs
are where the aggregate hides the trade:

- **The model team** owns the structure: the slice weights, the gating
  architecture, and the calibration layer. It owns the fix, and the
  slice-trades and gradient-conflict detours are its failure modes.
- **The evaluation team** owns the guardrail: the stratified AUC matrix by
  slice and task, the per-decile calibration slope, and the per-slice
  intervals. The audit's verdict is its signal, and it holds the gate
  before a model with a moved tail is released.
- **The product owner** owns the slice trade. Where to sit on the weight
  frontier is an experience decision — the tail slice's experience against
  the head slice's — that no single model metric decides, which is why the
  weight sweep's saturation point goes in front of product, not model.

When the ownership is implicit, the dashboard shows the aggregate AUC, the
model team tunes it, and nobody owns the tail — so a deliberate
reallocation reads as flat, a head model ships, and the tail loss is
called noise in the retro.

## Why this belongs in the mission

Every downstream stage multiplies this model's probabilities — the value
tree, the ads auction, the budget pacing — and a score that ranks fine but
is not a probability, or a slice whose trade was never measured, leaks
into every product of scores. This stage is where the mission's model
structure stops being an architecture choice and becomes an evaluation
contract.

## Evidence boundary

The executed synthetic read over 2,560 train rows with declared slice and
task rates (illustrative, deterministic, single seed). It demonstrates the
stratification and the three fixes; real systems must run the same audit
on production traffic — stratified by slice and task, with per-decile
calibration — and audit the learned gate weights before committing to
gating, since this cohort's gated variant lost to the explicit weight.

## Check your mental model

Answer each before opening it.

**1. Why does the aggregate AUC hide the seesaw?**

<details>
<summary>Answer</summary>

Because it is an exposure-weighted average: the dense head slice owns most
of the rows, so head movement dominates the number and the tail's loss is
averaged into noise. The executed audit shows aggregate click AUC moving
0.726 to 0.723 — flat — while tail click AUC gains 0.662 to 0.706 and head
click AUC pays 0.644 to 0.630.

</details>

**2. When does a gate (MMoE/PLE-style) not pay?**

<details>
<summary>Answer</summary>

When both tasks want the same representation. The gate collapses toward a
single expert and the architecture becomes a shared bottom with extra
parameters and serving cost. On this cohort the gated variant's buy AUC
(0.653) lost to explicit slice weighting (0.781); the diagnostic is the
learned gate weights, and the win condition is task disagreement.

</details>

## Next

Three executed failure faces: the weight dial itself — [the first steps
buy the tail cheaply and the aggregate does not move, then the frontier
saturates](when-the-slice-trades/) (tail 0.654 to 0.708, head 0.673 to
0.602, aggregate 0.735 to 0.704); the gradient-surgery promise — [the
gradients conflict in 43 of 60 epochs and PCGrad is still neutral, because
the sparse task's bottleneck is amplitude, not direction](when-the-gradients-conflict/);
and the calibration axis — [temperature scaling repairs the probability
mapping, but the layer is a second model with its own freshness
cost](when-the-second-model-costs/) (slope 1.098 to 0.983 fitted, broken
again by a shift the frozen temperature did not see).
