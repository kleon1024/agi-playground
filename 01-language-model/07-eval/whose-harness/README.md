---
status: draft
level: applied
base: scratch
label: Whose harness produced it
---

# Which part of a score belongs to the model?

In July 2026 OpenAI changed two settings in an ARC-AGI-3 evaluation harness and
watched GPT‑5.6 Sol go from **13.3% to 38.3%** on the public set — roughly three
times the score, using six times fewer output tokens, with the model completely
unchanged. Neither setting was a prompt. One retained the model's private
reasoning across turns instead of discarding it after every action; the other
compacted the context instead of dropping the oldest messages.

That is what a harness is worth. This chapter is about the half of a benchmark
number nobody names: what a harness owns, which of its settings have a right
answer, which only have a *declared* answer, and when to adopt someone else's
instead of writing your own.

**Before this:**
[how would you know if any of this worked?](../README.md), through the
perplexity section. You need the argument that a score without its conditions is
a number-shaped object; this chapter is what to do about it.

## What the harness owns

An agent benchmark score is a function of `(model, tools, system prompt,
loop/retry design, context-management policy, sampling parameters, environment
version)`. Seven terms, and published comparisons routinely disclose the first.

The ARC result is that argument with a number attached, and it splits cleanly
into two kinds of finding — which is the distinction the rest of this chapter is
built on. Discarding reasoning was close to a straight defect: the model is
trained to think privately and carry that thinking forward, so a harness that
throws it away is evaluating a different system than the one that shipped.
Truncation versus compaction is not a defect at all. It is a policy choice with
no universally correct value, and ARC and OpenAI picked opposite ones.

## Five things a good harness always does

These have no defensible alternative. Get one wrong and the harness is broken,
not merely configured differently.

**1. A stop condition the model does not control.** `run_agent` has two exits:
the model emits `Final Answer:`, or `max_steps` is reached. A loop with only the
first hangs the first time a model gets stuck retrying a failed action, which is
a normal outcome rather than a rare one.

**2. Grounding enforced, not requested.** The harness passes
`stop=["Observation:"]` so the backend stops at the boundary, *and* truncates
anything at or after that token unconditionally before parsing. The second layer
is the one that matters: a backend that ignores the stop sequence must not be
able to slip a fabricated observation into the trajectory. This is harness
discipline, not a model capability, and a smarter model does not remove the need
for it.

**3. A recovery path for every way a tool call can fail.** Schema adherence is
probabilistic. Invalid JSON, an unknown tool name, and a missing required
argument each become an *observation the model can act on* — never a crash. A
harness that dies on the first malformed call converts a model's ordinary
behavior into a harness failure and reports it as a score.

**4. State carried the way the model was trained.** This is the ARC lesson
generalized. If a model is trained to reason privately and reuse that reasoning
across turns, a harness that discards it between actions is not running a
stricter evaluation — it is running a different model. Match the deployment
contract, then evaluate.

**5. A transcript logged as a byproduct.** Disclosure that has to be assembled
after the run does not happen. inspect-ai (UK AISI) builds a whole framework
around this — dataset, solver, scorer, full transcript per run — and this stage
hand-rolls the same idea because the transcript schema here is its own.

## Four things a good harness declares instead

These have no correct value. What makes a harness good is that somebody chose on
purpose and wrote it down.

| Choice | Defensible positions |
|---|---|
| Context policy | drop oldest (ARC), compact (OpenAI), collapse superseded reads first ([stage 06](../../06-agent/what-fits-in-context/)) |
| Tool surface | three tools, because containment is easier; thirty, because the task needs them |
| Step and retry budget | generous, to see what the model can do; tight, to see what it does under pressure |
| Sampling | temperature and seed count, where a single run at temperature above zero is one draw from a distribution rather than the distribution |

And one meta-choice above all of them: **whether the harness is tuned to a
vendor at all.** ARC deliberately used a generic harness so shortcomings stay
visible and models stay comparable. OpenAI recommends the opposite — use the
settings a product actually deploys with. Both are coherent because they measure
different things: ARC measures the model, a tuned harness measures the product.
Neither is "the score," and a reader given one number has been handed a claim
about a pair.

## Disclosure as a validation check, not a paragraph

Saying all of that in a docstring changes nothing. `core/evaluate.py
agent-report` instead defines `REQUIRED_HARNESS_FIELDS` — `tools`, `max_steps`,
`context_budget_tokens`, `model_endpoint`, `temperature`, `harness_version`,
`seed` — and **raises** when a transcript is missing any of them.

Read that list against the table above: it is exactly the declared-choice column,
turned into a precondition. The argument becomes something a run cannot skip,
which is the only form of it that survives a deadline.

## Which harness should you reach for?

`prod/lm_eval.py` runs the same checkpoint through EleutherAI's
lm-evaluation-harness via a from-scratch adapter, `SpeedrunLM`, implementing the
three methods the harness needs — `loglikelihood`, `loglikelihood_rolling`,
`generate_until` — against
[`02-pretrain/core/model.py`](../../02-pretrain/core/model.py)'s `Transformer`.

| | Standard harness | Your own harness |
|---|---|---|
| The task is a fixed prompt with a fixed answer | yes, always | wasted work |
| The task is a trajectory with tools and state | it cannot express it | required |
| You want comparability to published numbers | that is the whole point | impossible |
| The transcript schema is yours | fights you | fits |

Writing one adapter buys hundreds of community-maintained static benchmarks,
comparable to every other model run at the same harness version and task
revision. What it cannot buy is a trajectory: lm-eval-harness scores one static
task at a time, with no multi-turn state, no tool calls, and no environment that
changes between steps. "Static benchmark" and "agentic trajectory" are different
measurement problems, not the same one at different scale.

So the honest default is both, for different halves of the report.

## Check your mental model

1. Name three of the seven components of an agent score that a "Model A beats
   Model B" claim usually leaves out.

<details>
<summary>Answer</summary>

The score is a function of `(model, tools, system prompt, loop/retry design,
context-management policy, sampling parameters, environment version)` — seven
terms — and published comparisons routinely disclose only the first. Any
three of the other six qualify: tools available, context-management policy
(the exact setting that took ARC's number from 13.3% to 38.3%), sampling
parameters (temperature and seed count), step/retry budget, system prompt,
or environment version. Leaving any of them undisclosed means "Model A beats
Model B" is really "this configuration of Model A beats that configuration
of Model B," which is a claim about a pair, not about the models alone.

</details>

2. Discarding reasoning and truncating context both cost points in the ARC
   result. Why does only one of them count as a harness defect?

<details>
<summary>Answer</summary>

Discarding the model's private reasoning between turns is close to a
straight defect because the model was trained to think privately and carry
that thinking forward — a harness that throws it away is evaluating a
different system than the one that actually shipped, per item 4 of "five
things a good harness always does." Truncating versus compacting context is
not a defect at all; it's a policy choice with no universally correct value.
ARC and OpenAI simply picked opposite ones, and both are defensible as long
as they're declared — the chapter's whole point is that "match the
deployment contract" has a right answer, while "how do you manage context"
does not.

</details>

3. Why does `REQUIRED_HARNESS_FIELDS` raise rather than warn, and what would
   change if it warned?

<details>
<summary>Answer</summary>

It raises because a warning can be ignored and a run can still complete and
get reported — the whole point of the check is to make disclosure a
precondition a run cannot skip, "the only form of it that survives a
deadline." If it only warned, a transcript missing `tools`, `max_steps`,
`temperature`, or any other required field could still produce a published
score with those seven components silently incomplete, which is exactly the
"number-shaped object" the previous chapter argues against. Raising forces
the choice to be made and recorded before the score exists at all.

</details>

4. ARC's generic harness and OpenAI's tuned one disagree. What does each one
   measure that the other cannot?

<details>
<summary>Answer</summary>

ARC's generic harness measures the model — deliberately using untuned
settings so shortcomings stay visible and different models stay comparable
against the same neutral conditions. OpenAI's tuned harness measures the
product — the settings a real deployment actually uses, including context
handling matched to how the model was trained. Neither can measure what the
other measures: a generic harness can't tell you how the model performs in
its actual deployment configuration, and a tuned harness can't give you a
model-only comparison uncontaminated by product-specific engineering. "Model
A beats Model B" from either one is a claim about that pair, not "the
score."

</details>

5. A colleague proposes evaluating your agent through lm-eval-harness. What is
   structurally wrong with that, and what is *not* wrong with it?

<details>
<summary>Answer</summary>

What's structurally wrong: lm-eval-harness scores one static task at a time
with a fixed prompt and fixed answer — it cannot express a trajectory with
tools, multi-turn state, and an environment that changes between steps.
"Static benchmark" and "agentic trajectory" are different measurement
problems, not the same one at different scale, so pointing it at an agent
loses everything the agent's own transcript would show. What's not wrong:
lm-eval-harness is exactly right for the checkpoint's static capability —
`prod/lm_eval.py` uses it for real, via the `SpeedrunLM` adapter, to get
comparability against hundreds of community-maintained benchmarks at a fixed
harness version, which a from-scratch agent harness could never offer. The
honest answer is both, for different halves of the report, not either
instead of the other.

</details>

## The fix and its trade

The failure mode is the half of a benchmark number nobody names: a score is
a function of (model, tools, system prompt, loop/retry design,
context-management policy, sampling parameters, environment version), and
published comparisons routinely disclose the first term. The measured
consequence is the ARC-AGI-3 result — two harness settings, model unchanged,
13.3% to 38.3% with six times fewer output tokens — and it splits cleanly:
discarding the model's private reasoning across turns is close to a straight
defect (the harness was evaluating a different system than the one that
shipped), while truncation versus compaction is a declared policy with no
universally correct value, where ARC and OpenAI picked opposite sides.

The fix is the split between what a good harness always does and what it
merely declares. Always: a stop condition the model does not control,
grounding enforced rather than requested, a recovery path for every way a
tool call can fail, state carried the way the model was trained, and a
transcript logged as a byproduct. Declared: context policy, tool surface,
step and retry budget, sampling — the no-correct-value column turned into a
precondition by `REQUIRED_HARNESS_FIELDS`, which raises rather than warns
because a warning can be ignored and the only disclosure that survives a
deadline is one a run cannot skip. The trade is that the two harness
philosophies measure different things: a generic harness (ARC) measures the
model, keeping shortcomings visible and models comparable; a tuned harness
(OpenAI) measures the product, using the settings a real deployment uses —
neither is "the score," and a reader handed one number has been handed a
claim about a pair. The standard-versus-own choice has the same shape:
lm-eval-harness buys comparability against hundreds of community-maintained
benchmarks at a pinned version (this stage's adapter ran `lambada_openai`
at 20.5% accuracy, 138.3 perplexity, after fixing two real adapter bugs),
but cannot express a trajectory with tools and changing environment, so the
honest default is both — static benchmarks and agentic trajectories are
different measurement problems, not one problem at different scale. The
ARC numbers are external and not reproducible here: the model is hosted,
and 38.3% remains below the 48% human estimate.

## Who owns the loop

- **The evaluation team** owns the harness contract: the five always-do
  items, the declared-choice column, and `REQUIRED_HARNESS_FIELDS` as the
  enforceability mechanism that makes disclosure a precondition of a score.
- **The model team** owns the deployment-contract match: state carried the
  way the model was trained is a defect boundary, not a configuration
  choice — a harness that discards private reasoning is running a different
  model.
- **The benchmarking-platform team** owns the standard-harness adapter and
  version pinning: harness version and task revision are part of the number,
  and comparability is worthless across an undated harness.
- **The product team** owns which measurement a release needs: model-only
  comparison (generic harness) versus product behavior (tuned harness), and
  the decision that the report carries both halves rather than one.

## Evidence boundary and next step

The ARC-AGI-3 numbers are external, published by the model's own vendor, and
not reproducible here: the model is hosted, the benchmark is not run in this
repository, and OpenAI's compaction item is encrypted, so what survived
compaction cannot be audited from outside.
[The research pass](../../../04-agentic-platform/harness-effects-landscape.md) records what the
result does and does not establish, including the fact that 38.3% remains below
the 48% human estimate.

Both halves of this stage's tooling have since run for real: `core/evaluate.py
agent-report` reports 0/6 ([the parent
chapter](../README.md#what-the-agent-report-actually-says)), and
`prod/lm_eval.py` scored the same checkpoint on `lambada_openai` at 20.5%
accuracy, 138.3 perplexity, limit 200 ([full
report](../runs/2026-07-30-lm-eval-lambada.md)) — after fixing two real bugs
that had silently kept the adapter from running at all (a self-import
collision from sharing its filename with the package it wraps, and a
read-only `device` property in the installed harness version). Neither number
says anything about frontier-scale capability; both confirm the adapters
this chapter argues for actually work end to end. The version of the ARC
experiment this repository *could* run is stated in that research pass:
stage 06's context policy is swappable by construction.

Return to
[what this mission's evaluation does not prove](../README.md#what-this-missions-evaluation-does-not-prove),
which is the boundary any report from either harness inherits.
