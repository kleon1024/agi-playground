---
status: verified
level: applied
base: scratch
label: AUC-label seesaw
verified: 2026-08-07
---

# Two objectives moved in opposite directions. What do you ship?

**Question:** one model predicts click and buy from the same embeddings.
You train it, click AUC goes up, buy AUC goes down. The click team wants
the new model; the buy team wants the old one. By what rule do you decide?

**Before this:** [stage 04 — fine-rank](../../shared/04-fine-rank/) for the
shared trunk both objectives read from, and [stage 61 — multi-task
conflict](../61-multi-task-conflict/) for why an abundant task shapes the
trunk these variants build on.

## The seesaw is a trade you choose, not a bug you fix

Industry already named this fight. Tencent's recommendation team described
exactly this pattern — one objective's AUC improves, another's falls — and
called it the seesaw (跷跷板) (Tang et al., PLE, RecSys 2020). It is not a
training mistake. The trunk is shared and the loss is one weighted sum, so
each gradient step is a compromise: it moves the representation toward
whichever objective contributed more to that step. Improve the buy task
and you pay with the click task. The trade is structural.

So the question is never "can we have both." It is "which position on this
trade are we choosing, and who decides?"

## The decision rule comes before training, not after

A seesaw is undecidable after the run, because the same numbers can be
argued in both directions — that is exactly the meeting that never ends.
The fix is a two-line contract written before training:

- **Primary metric** — the objective the model is being improved for.
- **Guardrails** — objectives that may not regress past a stated threshold.

Then the results decide themselves. Here are the demo's three variants (a
mechanism demo; see the evidence boundary at the end):

| variant | click AUC | buy AUC |
|---|---:|---:|
| shared trunk (baseline) | 0.726 | 0.716 |
| buy-weighted | 0.723 | 0.781 |
| expert-gated | 0.725 | 0.653 |

Two contracts, the same table, two different ships:

| contract | verdict |
|---|---|
| buy primary, click guardrail ≥ 0.720 | buy-weighted ships — buy 0.716 to 0.781, click clears the guardrail |
| click primary, buy guardrail ≥ 0.700 | nothing ships — buy-weighted regresses the primary, expert-gated breaches the guardrail (0.653) |

The numbers did not change; the objective did. When a team cannot agree
after the run, it is almost always because nobody wrote the contract down.
The failure is upstream of the model, in the objective definition — not in
the AUCs.

<!-- interactive: SeesawTradeoff -->

## Why one of them has to lose

Three mechanisms, in plain terms:

- **One gradient, many pulls.** The update is an average over samples.
  Click has an order of magnitude more positives than buy, so most of
  every step is spent fitting click. The sparse objective's signal is
  real but drowned.
- **Correlated labels are not the same label.** Click and buy overlap but
  describe different events; a representation that ranks clicks well does
  not automatically rank buys well.
- **One bottle.** The shared embeddings are a single capacity. Whatever
  the buy task gains must be taken from somewhere else — usually the tail
  of click.

None of these is a defect. They are the reason every position on the trade
is a real trade.

## You move along the trade; you do not delete it

- **The weight dial is the first fix.** Raise the buy task's weight and
  you walk along the frontier. The first steps buy the sparse tail
  cheaply, then the frontier saturates — [the weight frontier
  detour](when-the-slice-trades/) measures it. Where you stop is a product
  decision, not a model one.
- **Structure pays only when the dial cannot.** MMoE and PLE route tasks
  through separate experts when tasks genuinely need different expertise
  (Ma et al., KDD 2018; Tang et al., RecSys 2020). In the demo the gate
  lost to the explicit weight; the diagnostic is the learned gate weights
  — if they collapse onto one expert, the gate is a shared trunk with
  extra parameters.
- **Gradient surgery is the last resort.** PCGrad and its family change
  update directions to reduce conflict; they do not fix a sparse task
  whose bottleneck is gradient amplitude, not direction ([the
  gradient-surgery detour](when-the-gradients-conflict/)).

## The fix and its trade

The failure is not the trade — it is that the trade is undecidable after
the run. The same numbers can be argued in both directions, which is the
meeting that never ends, so the fix is a two-line contract written before
training: a primary metric and guardrail thresholds. The demo's three
variants make the rule concrete — shared trunk click 0.726 / buy 0.716,
buy-weighted 0.723 / 0.781, expert-gated 0.725 / 0.653 — and two
contracts ship different models from the same table: buy primary with a
click guardrail of at least 0.720 ships buy-weighted, click primary with
a buy guardrail of at least 0.700 ships nothing (expert-gated breaches
at 0.653). The trade is the structural price of one shared
representation: each gradient step is a compromise, click carries an
order of magnitude more positives than buy so most of every step fits
click, and whatever the buy task gains is taken from somewhere else. The
dials move along the trade without deleting it, and each has a measured
cost: the weight dial buys the sparse tail cheaply at first and then
saturates ([the slice-trades detour](when-the-slice-trades/)); structure
pays only when the dial cannot, and a learned gate that collapses onto
one expert is a shared trunk with extra parameters; gradient surgery is
the last resort, because PCGrad fixes gradient direction, not the sparse
task's amplitude bottleneck ([the gradients-conflict
detour](when-the-gradients-conflict/)). The decision rule itself follows
the guardrail-metric practice of Kohavi & Tang (2017): judge by
per-objective deltas with intervals, not by the primary's movement alone.

## Who owns the loop

- **Product owns the frontier position.** Which objective is primary, and
  where on the trade the system sits, is an experience and business
  decision. The weight sweep's saturation point goes in front of product,
  not the model team.
- **Evaluation owns the gate.** Per-objective deltas with confidence
  intervals and the guardrail thresholds. A declared guardrail that
  regressed blocks the ship, whoever likes the primary.
- **The model team owns the structure and the dial.** It builds the
  variants and sweeps the weights; it does not decide the preference.

When the ownership is implicit, the meeting is a debate: nobody owns the
guardrails, and the model that ships is whichever team argued loudest.

## What this chapter does not prove

The three variants run on a 2,560-row synthetic cohort: a mechanism demo
that makes the trade visible, not a production result. The decision rule
is the industrial practice — declare primary and guardrails before the
experiment, then judge by per-objective deltas with intervals (the
guardrail-metric practice follows Kohavi & Tang, *Trustworthy Online
Controlled Experiments*, 2017). Calibration — whether the score is a real
probability, separate from whether it ranks well — is another axis
entirely, covered in [the calibration detour](when-the-second-model-costs/).

## Check your mental model

**1. Why does the same table ship different models under two contracts?**

<details>
<summary>Answer</summary>

Because the contract is the decision and the table is only evidence.
Primary metric plus guardrail thresholds turn "some objectives went up,
some went down" into a pass/fail rule. Without the contract, the same
numbers can be argued in either direction — the meeting that never ends.

</details>

**2. Is the seesaw a model bug?**

<details>
<summary>Answer</summary>

No. It is a structural property of one shared representation serving
multiple objectives. The bug is usually the missing decision contract,
written after the run instead of before it.

</details>

## Next

Return to [stage 61](../61-multi-task-conflict/), or go deeper: the
[weight frontier](when-the-slice-trades/), the [gradient-surgery
promise](when-the-gradients-conflict/), and the [separate calibration
axis](when-the-second-model-costs/). When an objective's slice has so few
positives that its interval spans chance, the seesaw is the least of your
problems: [stage 65 — sparse labels](../65-sparse-labels/).
