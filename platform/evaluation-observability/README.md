---
status: draft
---

# 07 — Evals

## Why this track exists

"My model scores 68% on benchmark X" is a claim that has quietly become
harder to interpret every year, and this track exists to teach the specific
reasons why, not just the tools that produce the number. Static-benchmark
evaluation (perplexity, task suites, multiple-choice accuracy) is
well-understood and this track covers it, but the harder, less-served
problem — flagged consistently across the four research surveys behind
this repo — is agentic evaluation: once you're scoring a model *plus a
harness* (a loop, a tool set, a context-management strategy) acting in an
environment over many turns, the harness is not a footnote to the result,
it is an independent variable in it. A 2026 paper made this the title of
its argument: *"Stop Comparing LLM Agents Without Disclosing the Harness."*
This track takes that seriously as its organizing idea, alongside the
adjacent, equally under-taught problems of benchmark contamination,
LLM-as-judge bias, and the statistical noise that makes small-sample eval
comparisons look more decisive than they are.

## What you build

**Speedrun stage [07 — eval](../../missions/01-language-model-agent/07-eval/)** is this track's
integration point: the final report across every prior speedrun stage —
perplexity on the pretrained checkpoint, a small task suite via lm-eval-
harness, and a harness-disclosed evaluation of the stage 06 agent — is
lesson `06-building-an-eval-report` below, run against the speedrun's own
model and harness rather than a third-party one. This is also the stage
that makes the rest of the speedrun honest: if you can't produce a real,
reproducible number for a stage, the speedrun's own rule (see the top-level
README's "How lessons work") says that stage doesn't get to claim a result.
This track deepens starting at milestone **M5**, per the roadmap, alongside
`08-agents` — the two tracks share the harness-disclosure argument, from
opposite sides (this track scores the harness; that one designs it).

## The conceptual spine

### 1. Static benchmarks vs. agentic evals — a real distinction, not a scale difference

A static benchmark scores one forward pass (or one greedy/sampled
completion) against a fixed answer: perplexity on held-out text, accuracy
on a multiple-choice task, pass@k on a coding problem. The evaluation
target is the model. An agentic eval scores a *trajectory* — a sequence of
observe→act→observe steps through an environment, where intermediate steps
matter, multiple paths can be correct, and the environment's state, not
just the final output, determines success. The evaluation target is
model-plus-harness, and that's not a minor footnote: the same underlying
model wrapped in two different harnesses (different tool schemas, different
retry logic, different context-window management) can produce meaningfully
different scores on the identical benchmark. This track treats the two
regimes as needing genuinely different methodology, not the same accuracy
computation run on harder tasks.

### 2. The two reference frameworks: lm-eval-harness and inspect-ai

**lm-evaluation-harness** (EleutherAI) is the standard for static/non-
agentic benchmarks: task definitions are declarative (a YAML/Python spec
naming the dataset, the prompt template, the scoring function — exact
match, log-likelihood comparison for multiple choice, or a custom metric),
which is what makes it possible to add a new benchmark without touching the
harness's execution engine. **inspect-ai** (UK AISI) generalizes this
pattern to agentic and tool-using evaluation: a task is a `dataset` + a
`solver` (the thing that can loop, call tools, manage multi-turn state) +
a `scorer`, and every run produces a full transcript log — every model
call, every tool call, every intermediate score — not just a final number.
That transcript is what makes harness-disclosed reporting possible in
practice: you can't disclose what you didn't record. This track teaches
both directly, at small scale (a handful of tasks, one model, one harness
configuration) rather than reimplementing either — unlike most of this
curriculum's tracks, there's no from-scratch/production split here, because
both frameworks *are* the production tooling, and reimplementing an eval
harness from scratch teaches far less than running the real one correctly
(see `LANDSCAPE.md`).

### 3. Contamination: why SWE-bench Verified is distrusted and SWE-bench Pro exists

SWE-bench (Jimenez et al., 2024) — real GitHub issues paired with the PR
that fixed them, scored by whether a generated patch makes the associated
test suite pass — became the closest thing coding agents have to a gold-
standard benchmark. SWE-bench Verified, a human-filtered 500-issue subset
meant to remove ambiguous or under-specified issues, became the number
everyone quoted. The problem that has since surfaced: the underlying
repositories and their fix PRs are public GitHub content, and models
trained on post-cutoff web/code data have plausibly seen the *answers*, not
just the *questions* — contamination that a fixed, published benchmark
cannot self-correct for once it's been in enough training corpora. SWE-bench
Pro is the documented response: a successor built from private or otherwise
undisclosed repositories specifically so the fix isn't sitting in anyone's
training set. The general lesson generalizes past this one benchmark pair:
any benchmark built from public, static content has a shelf life, and
"widely cited" is not the same claim as "uncontaminated."

### 4. Harness disclosure: the independent variable nobody reports

The 2026 argument this track is named after is straightforward once stated:
an agent benchmark score is a function of (model, tool set, system prompt,
loop/retry design, context-management strategy, sampling parameters,
environment version) — and most published comparisons report only the
first. Two papers claiming "Model A beats Model B on Benchmark X" using
different scaffolds are not making a comparable claim, even if the
benchmark name is identical. GAIA (general assistant tasks, exact-match
scored) is explicitly flagged in the literature as harness-sensitive for
exactly this reason — its own authors note scaffold matters enough that
cross-paper score comparisons need the scaffold controlled for, not just
the model. This track's practical response, taught in
`05-harness-disclosed-agent-evals`, is a reporting discipline: pin and
publish the tool schemas, the loop structure, the context-window policy,
and the retry/timeout limits alongside every agentic eval number — treating
the harness as a first-class part of the experimental setup, the way you'd
disclose hyperparameters for a training run.

### 5. LLM-as-judge: known, reproducible failure modes

Wherever an open-ended answer needs scoring — alignment evals (MT-Bench,
AlpacaEval-style pairwise comparison), preference-data labeling, agentic
trajectory grading — an LLM judge is standing in for the human evaluator
that doesn't scale, and it inherits well-characterized biases rather than
neutral judgment: **position bias** (favoring whichever response is shown
first — mitigated by scoring both orderings and discarding disagreements),
**length/verbosity bias** (favoring longer or more elaborately formatted
answers independent of quality — AlpacaEval 2.0's length-controlled win
rate is a direct, quantified correction for this), **self-enhancement
bias** (a judge favoring outputs from its own model family — mitigated by
using a different model as judge than as generator), and **format bias**
(favoring markdown-structured answers over equally correct prose). None of
these are solved by a better-worded judge prompt alone; they require
structural countermeasures — swapped-order scoring, length control,
cross-model judging, multi-judge voting — and this track teaches the
detection protocol (hold out ~100 human-labeled gold examples, measure
judge-human agreement, inspect the disagreement pattern for exactly these
signatures) as a required step before trusting a judge pipeline's output.

### 6. Statistical significance and variance across seeds

A single eval run on a few hundred samples produces a point estimate with a
confidence interval wide enough to make most reported leaderboard
differences statistically meaningless: 300 samples at a 50% success rate
carries a 95% bootstrap CI of roughly ±5.7 points, meaning two agents
separated by 4 points on that benchmark are not distinguishable from noise
without a larger sample or a paired comparison. Agentic evals compound this
with genuine run-to-run variance beyond sampling — nonzero temperature,
environment nondeterminism, and multi-turn compounding of small per-step
differences all mean the same agent scored twice can land in different
places. The practical discipline this track teaches: bootstrap confidence
intervals as a default reporting artifact (not an optional appendix), and
where possible, multiple seeds/rollouts per task with variance reported
alongside the mean — a single number without either is not a claim you can
compare against anyone else's single number.

Change the task count below and watch twelve repeat estimates converge. This is
the sampling-noise baseline you must understand before attributing a small score
gap to a model or harness change.

<!-- interactive: EvaluationUncertainty -->

### 7. τ²-bench-style policy-adherence environments

Most agent benchmarks score task completion — did the agent get the right
final state. τ-bench and its successor τ²-bench (Sierra Research) add a
dimension most benchmarks skip: **policy adherence** as an independent
pass/fail criterion, not just an implicit part of "did it work." A telecom-
support agent that resolves a customer's issue by violating a stated policy
(refunding outside policy limits, sharing account data without verification)
has failed the environment even though the task outcome looks successful.
τ²-bench's dual-control design (both the simulated user and the agent can
invoke tools) further stresses realistic multi-turn tool-use dynamics that
single-actor benchmarks don't exercise at all. This is the template this
track uses for "environment + policy" as its own evaluation design pattern,
distinct from simple task-success scoring, and it's directly relevant to
any agent harness (see `08-agents`) meant to operate under real-world
constraints rather than a sandboxed task-completion game.

## Planned lessons

1. `01-perplexity-and-lm-eval-harness` — standard language-model
   evaluation: perplexity computation and task-suite scoring via
   lm-eval-harness.
2. `02-task-suites-with-inspect-ai` — structured, transcript-logged eval
   design with inspect-ai; tasks, solvers, scorers.
3. `03-llm-as-judge-and-alignment-evals` — MT-Bench/AlpacaEval-style
   pairwise and absolute scoring, the standard bias catalogue (position,
   length, self-enhancement, format), and detection/mitigation protocol.
4. `04-statistical-significance-and-variance` — bootstrap confidence
   intervals, sample-size effects on distinguishability, and variance
   across seeds/rollouts in agentic evals.
5. `05-harness-disclosed-agent-evals` — why agent benchmark comparisons
   must disclose harness design (tools, loop, context management) as an
   independent variable; contamination case study (SWE-bench Verified vs.
   SWE-bench Pro); τ²-bench-style policy-adherence environment design.
6. `06-building-an-eval-report` — assembling an honest, reproducible eval
   report spanning perplexity, task suite, and harness-disclosed agent
   eval. Seeds speedrun stage 07.

## Common misconceptions

- **"A benchmark score is a property of the model."** For agentic
  benchmarks it's a property of the model *and* the harness jointly — the
  same model under two scaffolds can post materially different numbers on
  the identical benchmark, which is precisely the argument this track is
  named after.
- **"SWE-bench Verified is still the reliable number to quote."** Its
  public, static nature makes it contamination-prone in a way its
  human-filtering pass doesn't fix; SWE-bench Pro exists specifically
  because the field needed a benchmark whose answers aren't already
  circulating in training corpora.
- **"An LLM judge is a neutral proxy for human preference."** It carries
  the same reproducible bias catalogue as human-annotation pipelines
  (position, length, self-enhancement, format) and needs the same
  structural countermeasures, not a better prompt.
- **"A single eval run is the answer."** Without a confidence interval or
  multi-seed variance, a reported score is a point estimate whose precision
  is usually much lower than the leaderboard-style ranking implies —
  300-sample benchmarks routinely carry ±5-6 point 95% CIs.
- **"Task completion is the whole evaluation."** Policy adherence (did the
  agent stay within stated constraints while completing the task) is a
  separate, and sometimes contradictory, axis — τ²-bench's dual-control,
  policy-scored design exists because task-success-only scoring misses
  exactly this failure mode.

## Prerequisites

None strictly required to start — evals can run against any checkpoint or
agent. In practice this track is most useful once you have a model from
`03-pretraining` (or later) and/or an agent harness from `08-agents` to
evaluate against.

## Key papers

- Zheng et al., *"Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"*
  (2023) — the original catalogue of LLM-judge biases and the ELO-based
  Arena methodology; the reference point for lesson 3.
- Jimenez et al., *"SWE-bench: Can Language Models Resolve Real-World
  GitHub Issues?"* (ICLR 2024) — the benchmark whose contamination story
  motivates lesson 5's case study.
- *"Stop Comparing LLM Agents Without Disclosing the Harness"* (2026) —
  the paper this track's central argument is drawn from; required reading
  before lesson 5.
- Sierra Research, *τ²-bench* (2026) — dual-control, policy-adherence-scored
  multi-turn tool-use evaluation; the template for lesson 5's environment-
  design exercise.
- Mialon et al., *"GAIA: A Benchmark for General AI Assistants"* (2023) —
  general-assistant task evaluation with an explicit, literature-noted
  harness-sensitivity caveat.

## Next

Read [speedrun stage 07 — eval](../../missions/01-language-model-agent/07-eval/) once the earlier
speedrun stages exist — this track's final lesson is that stage's report.
