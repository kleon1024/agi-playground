---
status: draft
level: applied
base: scratch
label: Whose harness produced it
---

# Which part of a score belongs to the model?

A benchmark number is produced by a model *and* a harness, and only one of
those two is usually named. This chapter is about the other one: what a harness
contributes to a score, how to force it into the record, and when to adopt
someone else's instead of writing your own.

**Before this:**
[how would you know if any of this worked?](../README.md), through the
perplexity section. You need the argument that a score without its conditions
is a number-shaped object; this chapter is what to do about it.

## Disclosure as a validation check, not a paragraph

An agent benchmark score is a function of `(model, tools, system prompt,
loop/retry design, context-management policy, sampling parameters, environment
version)`. Disclosing only the model name discloses the smallest part of what
produced the number.

Saying that in a docstring changes nothing. `core/evaluate.py agent-report`
instead defines `REQUIRED_HARNESS_FIELDS` — `tools`, `max_steps`,
`context_budget_tokens`, `model_endpoint`, `temperature`, `harness_version`,
`seed` — and **raises** when a transcript is missing any of them. The argument
becomes a precondition rather than advice, which is the only form of it that
survives a deadline.

This is the discipline inspect-ai (UK AISI) builds a framework around: dataset,
solver, scorer, with every run logging a full transcript so disclosure is a
byproduct of how the run was recorded rather than something added afterwards.
This stage hand-rolls the same idea at the scale one mission needs, because the
transcript schema here is this mission's own.

## What a standard harness buys, and where it stops

`prod/lm_eval.py` runs the same checkpoint through EleutherAI's
lm-evaluation-harness via a from-scratch adapter, `SpeedrunLM`, implementing the
three methods the harness needs — `loglikelihood`, `loglikelihood_rolling`,
`generate_until` — against
[`02-pretrain/core/model.py`](../../02-pretrain/core/model.py)'s `Transformer`,
the way `lm_eval.models.huggingface.HFLM` does it against a HuggingFace model.

**What that buys.** Task definitions are declarative: dataset, prompt template,
scoring rule. Write *one* model adapter and you can run hundreds of
community-maintained static benchmarks, with results directly comparable to
every other model run through the same harness version and task revision. The
alternative is one scoring function per benchmark and no comparability at all.

**Where it stops, structurally.** It scores one static task at a time — a fixed
prompt in, a score out. There is no notion of a multi-turn trajectory, no tool
calls, no environment state that changes between steps. Running a checkpoint
through lm-eval-harness establishes nothing about how it behaves as an agent.

That is why the two stay separate tools. "Static benchmark" and "agentic
trajectory" are different measurement problems, not the same problem at
different scale, and a harness built for the first will quietly report a
misleading answer to the second.

## Which one should you reach for?

| | Standard harness | Your own harness |
|---|---|---|
| The task is a fixed prompt with a fixed answer | yes, always | wasted work |
| The task is a trajectory with tools and state | it cannot express it | required |
| You want comparability to published numbers | that is the whole point | impossible |
| The transcript schema is yours | fights you | fits |

The honest default is both, for different halves of the report — which is
exactly what this stage does.

## Check your mental model

1. Name three components of an agent score that a "Model A beats Model B"
   claim usually leaves out.
2. Why does `REQUIRED_HARNESS_FIELDS` raise rather than warn, and what would
   change if it warned?
3. `SpeedrunLM` implements three methods. What does implementing them buy that
   writing three scoring functions would not?
4. A colleague proposes evaluating your agent through lm-eval-harness. What is
   structurally wrong with that, and what is *not* wrong with it?

## Evidence boundary and next step

Nothing here has been run. `prod/lm_eval.py` and `core/evaluate.py
agent-report` both execute, but no report exists in `runs/`, so this chapter
establishes what the tooling enforces — not what the model scores.

Return to
[what this mission's evaluation does not prove](../README.md#what-this-missions-evaluation-does-not-prove),
which is the boundary any report from either harness inherits.
