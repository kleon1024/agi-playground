---
status: verified
level: applied
base: scratch
label: The annealed slice moves the evals
verified: 2026-08-08
---

# When the annealed slice moves the evals

**Question:** mid-training's section 7 reports the mix as a fact — a
single-digit-percent agentic share, concentrated in the annealing phase.
This chapter asks the question behind the fact: what actually happens to
the model's evals when that share changes, and how does anyone decide
where the number stops? The answer, measured, is a seesaw: the agentic
slice rises fast at first, the general slice pays a flat recency-weighted
cost the whole way, and a blended aggregate rewards exactly the move that
breaks the contract.

**Before this:** [mid-training](../) for the stage and its reported mix
figures, and [the corpus mixture chapter](../../../00-corpus/what-a-release-needs/)
for why mixture weights have to be named. This chapter is the decision
the named weights exist to make.

## The audit, executed

The run ([record](runs/2026-08-08-mix-seesaw.md)) builds the seesaw
explicitly: an anneal window of 20,000 docs, a declared agentic share
from 0 to 10 percent, and two skill axes the window teaches. Agentic
skill saturates — the first points of share buy most of the capability.
General skill loses with a recency multiplier: displaced general tokens
in the final window hurt more than uniform displacement, because annealed
tokens dominate the final checkpoint. Sweeping the share against a
pre-declared guardrail (general eval stays within 10% of baseline):

| share | agentic eval | general eval | verdict |
|---|---:|---:|---|
| 0% | 0.000 | 1.000 | baseline |
| 3% | 0.699 | 0.952 | within guardrail |
| 5% | 0.865 | 0.920 | within guardrail |
| 8% | 0.959 | 0.872 | guardrail breach |
| 10% | 0.982 | 0.840 | guardrail breach |

Two numbers carry the story. The guardrail binds at 8 percent — the
general slice falls below its floor while the agentic eval is still 0.959
of a saturating curve, so "keep raising the share" is buying points that
are almost free to lose. And the marginal trade flips in the same band:
one point of agentic share buys 3.15 of agentic eval in the 5-8% range but
1.12 at 8-10%, against a flat 1.60 general-eval cost — the reported
single-digit practice band is exactly where the trade stops paying.

## The failure mode, named

The mix looks like a pipeline detail and is a multi-objective decision.
Real data-mixing evidence keeps showing that small curation choices move
downstream evals measurably: DCLM's scaling experiments tie data-curation
budget to eval performance (Li et al., "DataComp-LM," arXiv:2406.11794,
Jun 2024), FineWeb-Edu's ablations show filtering changes performance in
either direction (Penedo et al., arXiv:2406.17557, Jun 2024), and DoReMi
shows domain reweighting moving a model's evals across tasks (Xie et al.,
arXiv:2305.13029, May 2023). Yet the default in most pipelines is to set
the mix by hand once and never re-decide it — which is a decision made by
accident, because the person who sets it usually watches one eval.

The failure has three layers, and this run names each one. First, the
seesaw itself: raising the agentic slice moves two evals in opposite
directions, so "did the mix get better" has no single answer until someone
declares which eval is primary. Second, the recency asymmetry: because the
slice is annealed, its displacement of general text costs more than its
share suggests — the final tokens dominate the checkpoint. Third, the
aggregate blindness: the blended number rises through the breach (0.892 at
5% to 0.916 at 8%), so a team that watches one blended metric is rewarded
for exactly the move that violates the contract. The slice read — agentic
and general measured separately — is the only thing that sees it.

The zero-share anchor is not hypothetical. The agent stage's measured run
scored 0/6 against a checkpoint that never saw an agentic-formatted
example ([stage 06](../../../06-agent/)): at s = 0 the agentic eval is
zero, which is the reason the mix exists at all.

## The fix and its trade

The fix is the same contract this curriculum already uses for the
recommendation seesaw ([the AUC-label seesaw](../../../../02-personalized-discovery/recommendation/64-auc-label-seesaw/)):
before the mix moves, declare which eval is primary and set a guardrail
threshold on the others. Here: primary = agentic capability, guardrail =
general eval within 10% of baseline. The sweep then answers the question
directly — the guardrail binds at 8%, so the safe band is 5-8%, and the
knee says why: past it, each point of share buys less than it displaces.

The trade, named: a guardrail caps the secondary objective by contract,
which means the mix stops being a knob anyone can turn to chase a metric
that happens to be green this week. The agentic slice is capped at the
point where the general eval still holds, not at the point where the
agentic eval peaks — the model deliberately does not get the last few
points of agentic capability. That is the same price the recommendation
chapter names: a guardrail that never binds is not a guardrail, and one
that binds is a limit someone has to defend to the team that wants the
metric up. The second trade is attribution: a declared contract is only
useful if the eval set is stable, which is why the mix decision and the
eval read belong to different teams (below).

## Who owns the loop

The mix is a data-health decision with a three-way handoff:

- **The data-pipeline team** owns the mix weights and the anneal schedule:
  the share, the placement (annealing, not uniform), and the trajectory
  sourcing behind the slice. It owns the number, but not the target —
  deciding both is how the knob gets turned by the person watching one
  eval.
- **The evaluation team** owns the slice read: agentic and general evals
  measured separately, plus the guardrail thresholds, and the rule that a
  mix change re-runs both evals before it is accepted. It owns the
  case-finding step the aggregate cannot do.
- **The model team** owns the contract: which eval is primary, where the
  guardrail binds, and the pre-declared decision that turns "some up, some
  down" into pass/fail. When the ownership is implicit, the mix is set by
  whoever last touched the config, and the general slice falls below its
  floor with no number anywhere that says so.

## Evidence boundary

The executed read is a mechanism demo, not a trained model: the two curves
are declared formulas (`A(s) = 1 - exp(-40s)`, `G(s) = 1 - 1.6s`) chosen
to make the seesaw legible at toy scale, and the exact rates do not
transfer. What transfers is the shape of the failure — a saturating slice,
a flat recency-weighted cost, an aggregate that hides the falling slice —
and the contract that catches it. The training-scale claims the chapter
reasons about are cited, dated external results: Agentic CPT's 300B-token
budget (arXiv:2509.13310, 2025), GLM-5's mid-training at roughly 5% of the
pretraining budget (Kili Technology, 2026), and the mixing evidence of
DCLM, FineWeb-Edu, and DoReMi (above). No model was trained here.

## Check your mental model

Answer each before reading on.

**1. Why does the guardrail bind at 8% while the agentic eval is still
climbing?**

Because the two curves have different shapes: agentic skill saturates
(0.959 of the way at 8%) while general skill pays a flat recency-weighted
cost every point of the way. The last points of agentic share buy almost
no new capability and cost a full share of general eval — the decision is
where the guardrail says stop, not where the primary metric peaks.

**2. Why can a blended eval reward the move that breaks the contract?**

Because the blended number sums the two slices, and the rising slice hides
the falling one: it climbs from 0.892 at 5% to 0.916 at 8% — the breach
point — so a team watching only the blend sees improvement where the slice
read sees a violation. Aggregates reward the average; the contract has to
be enforced on the slice that pays the cost.

**3. What is the same pattern in the recommendation system, and what does
the shared contract look like?**

The AUC-label seesaw: multiple objectives, one shared model, and the
"some up, some down" question with no single answer. The shared fix is the
pre-declared contract — primary metric plus guardrail thresholds — which
turns the seesaw into a pass/fail decision both teams can defend. The mix
decision here is that contract applied to data instead of loss weights.

## Next

Back to [mid-training](../), where section 7's reported mix figures are
now the decision this chapter executes, and section 5 shows what the
agentic slice is made of — the three trajectory families, with truncation
and noise rendered. The failure-recovery half of that slice is measured in
the agent stage's [when the tool errors](../../../06-agent/when-the-tool-errors/),
and the corpus half of dirty-data washing — the filter that eats a whole
signal class — is [when the filter eats the signal](../../../00-corpus/when-the-filter-eats-the-signal/).
