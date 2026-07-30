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
2. Discarding reasoning and truncating context both cost points in the ARC
   result. Why does only one of them count as a harness defect?
3. Why does `REQUIRED_HARNESS_FIELDS` raise rather than warn, and what would
   change if it warned?
4. ARC's generic harness and OpenAI's tuned one disagree. What does each one
   measure that the other cannot?
5. A colleague proposes evaluating your agent through lm-eval-harness. What is
   structurally wrong with that, and what is *not* wrong with it?

## Evidence boundary and next step

The ARC-AGI-3 numbers are external, published by the model's own vendor, and
not reproducible here: the model is hosted, the benchmark is not run in this
repository, and OpenAI's compaction item is encrypted, so what survived
compaction cannot be audited from outside.
[The research pass](../../../../research/06-harness-effects.md) records what the
result does and does not establish, including the fact that 38.3% remains below
the 48% human estimate.

Nothing in this stage has been run either. `prod/lm_eval.py` and
`core/evaluate.py agent-report` both execute, but no report exists in `runs/`,
so this chapter establishes what the tooling enforces — not what the model
scores. The version of the ARC experiment this repository *could* run is stated
in that research pass: stage 06's context policy is swappable by construction.

Return to
[what this mission's evaluation does not prove](../README.md#what-this-missions-evaluation-does-not-prove),
which is the boundary any report from either harness inherits.
