---
status: draft
base: scratch
---

# How would you know if any of this worked?

**Goal:** produce one honest evaluation report for everything this speedrun
built, and make the report format itself refuse the claims it cannot support.

"My model scores 68% on benchmark X" is a sentence that looks precise and
usually isn't. It is missing the tokenizer and context length perplexity was
measured at, the harness (tools, loop, retries, sampling temperature) an
agent score was produced under, how many seeds were run, and what it beat.
Any one of those left out turns a number into a number-shaped object. This
stage is not a script that computes a score — it is a script that computes a
score *and refuses to emit it* when the surrounding disclosure is missing,
because that discipline is the actual lesson, and a docstring saying "please
disclose your harness" that nobody enforces teaches nothing.

## What you build

`core/evaluate.py` — three subcommands, one report format:

- **`perplexity`** — cross-entropy on a held-out token stream, converted to
  perplexity. Requires `--tokenizer` (sha256 goes in the report) and records
  the context length scored at — both load-bearing, see below.
- **`tasks`** — a small suite (JSONL) sized for what this mission's 88M
  checkpoint can plausibly attempt: `loglik` instances (which choice gets the
  highest log-probability, scored deterministically, reported with a
  bootstrap CI) and `generate` instances (sampled at temperature > 0, so a
  single run is a coin flip on that run's seed — `--seeds >= 3` is mandatory
  whenever the suite has any, and the script raises rather than accepting
  one).
- **`agent-report`** — aggregates harness-disclosed transcripts from stage
  06's agent. Every transcript must carry a `harness` block (tools, max
  steps, context budget, model endpoint, temperature, harness version, seed);
  missing any field, or fewer than 3 rollouts for any task, raises instead of
  summarizing.

Every subcommand also requires a named baseline (`--baseline-name/-value
/-source`) and writes a machine-readable `.json` plus a human-readable `.md`
summary, both ending in a `does not prove` section for that eval type.

`prod/lm_eval.py` — the same checkpoint through EleutherAI's
lm-evaluation-harness, via a from-scratch adapter (`SpeedrunLM`) implementing
the three methods the harness needs (`loglikelihood`, `loglikelihood_rolling`,
`generate_until`) against `02-pretrain/core/model.py`'s `Transformer`, the way
`lm_eval.models.huggingface.HFLM` does it against a HuggingFace model. What
that buys and what it doesn't is its own section below.

## Why "68% on benchmark X" is nearly uninterpretable

Break the sentence into what it needs to actually mean something:

1. **Which harness, exactly?** For anything beyond a single forward pass —
   any agent, any multi-turn task — the score is a function of (model, tool
   schemas, system prompt, loop/retry design, context-management policy,
   sampling parameters, environment version), and most published numbers
   disclose only the first. The 2026 paper this stage's track is named
   after, *"Stop Comparing LLM Agents Without Disclosing the Harness,"* is
   the argument in one sentence: two papers reporting "Model A beats Model B
   on Benchmark X" under different scaffolds aren't making a comparable
   claim, even with an identical benchmark name. GAIA's own authors flag
   their benchmark as harness-sensitive for exactly this reason.
2. **How many seeds?** A single run at nonzero temperature — or through any
   environment with real nondeterminism — is one draw from a distribution,
   not the distribution. `core/evaluate.py` raises rather than accepting
   `--seeds 1`.
3. **Beats what?** A score with no named baseline is not a comparison, it's
   a number; `require_baseline()` raises on every subcommand without one.
4. **Scored how?** Exact match, log-likelihood ranking, and an LLM judge are
   three different instruments with different failure modes (below);
   quoting a percentage without saying which one hides which failure mode
   might be operating.

None of these are exotic fixes. They're just usually left out, and each
omission independently makes the number harder to compare to anything.

## Perplexity depends on the tokenizer and the context length — always name both

Perplexity is `exp(mean cross-entropy per token)`. Both halves of that
definition are silently model-specific:

- **The tokenizer decides what a "token" is.** A larger vocabulary packs more
  characters per token (stage 01 measured 4.497 chars/token at 16,384
  vocab). Fewer, denser tokens change what "per-token" cross-entropy
  averages over — a coarser tokenizer can post a *lower* perplexity on the
  same text for reasons that have nothing to do with how well it predicts
  that text, purely because each token is a bigger, more predictable chunk.
  Comparing perplexity across two tokenizers compares two different units
  and calls them the same one.
- **Context length decides how much the model gets to condition on.** 128
  tokens of context and 4096 tokens of context on the identical model and
  text produce different numbers, because more context is (usually) less
  surprising. A "perplexity went down" claim between runs at different
  context lengths is not evidence the model improved.

This is why `core/evaluate.py perplexity` writes the tokenizer's sha256 and
exact context length into every report, not as metadata but as the condition
under which the number may be compared to anything else. A perplexity
number with neither recorded isn't wrong, exactly — it just isn't attached
to anything.

## Contamination: why SWE-bench Verified is distrusted and what replaced it

SWE-bench (Jiménez et al., 2024) scores whether a generated patch makes a real
GitHub issue's associated test suite pass. SWE-bench Verified — a
human-filtered 500-issue subset meant to remove ambiguous issues — became the
number everyone quoted for coding agents. The problem that surfaced after: the
repositories and their fix PRs are public, and a model trained on post-cutoff
web/code data has plausibly seen the *answer*, not just the question, on some
fraction of those 500 issues — and a static, published benchmark cannot
self-correct for that once it's sitting in enough training corpora.
**SWE-bench Pro** is the field's documented response — built from private or
otherwise undisclosed repositories so the fix isn't already circulating — and,
as of 2026, **Terminal-Bench 2.0** is cited alongside it as a successor
generation of agentic coding/terminal benchmarks built with the same
contamination lesson in mind. Attribute and date any number you quote from
any of these three: "SWE-bench Verified, as reported in [paper], [year]" is a
specific, checkable claim; "SWE-bench" bare is not, because the benchmark's
trustworthiness has visibly shifted across these versions in a few years. The
lesson outlives this benchmark family: any static, public benchmark has a
shelf life, and "widely cited" isn't the same claim as "uncontaminated."

## LLM-as-judge: known, reproducible failure modes

Wherever an open-ended answer needs scoring — this mission's model's
generations, an agent's free-form final response — an LLM judge substitutes
for a human rater and inherits specific, well-characterized biases rather
than neutral judgment (Zheng et al., 2023, the MT-Bench/Chatbot Arena paper):
**position bias** (favoring whichever response is shown first — mitigated by
scoring both orderings and discarding cases where the verdict flips),
**verbosity bias** (favoring longer or more elaborately formatted answers
independent of correctness — AlpacaEval 2.0's length-controlled win rate is a
direct, quantified correction), and **self-preference bias** (a judge
favoring outputs from its own model family — mitigated by judging with a
different model than the one that generated the answer). None of these are
solved by a better-worded judge prompt; they need structural countermeasures
(swapped-order scoring, length control, cross-model judging), and the
detection protocol is concrete: hold out a small human-labeled gold set,
measure judge-human agreement, and inspect disagreements for exactly these
signatures before trusting the judge's output on anything you can't check by
hand.

## Statistical significance: why one seed lies

A point estimate from a few hundred samples carries a confidence interval
wide enough to make most reported differences look more decisive than they
are: 300 samples at a 50% success rate carries a roughly ±5.7-point 95%
bootstrap CI, so two runs 4 points apart at that sample size aren't
distinguishable from noise. Agentic evals compound this with genuine
run-to-run variance beyond sampling — nonzero temperature, environment
nondeterminism, and multi-turn compounding of small per-step differences all
mean the identical agent scored twice can land in different places for
reasons unrelated to anything you changed. `core/evaluate.py` takes two
different, non-interchangeable positions on this: a bootstrap CI over the
fixed set of `loglik` instances (uncertainty about which instances you
happened to sample) and mean ± std over `--seeds` real sampled rollouts for
`generate` instances and agent transcripts (uncertainty about what the model
does on repeated attempts at the *same* instance). A report with neither is
a number this stage's tooling will not produce.

Change the task count below and decide when a four-point difference becomes
meaningful. The repeated bars hold the system fixed and vary only the sample.

<!-- interactive: EvaluationUncertainty -->

## The harness-disclosure argument, operationalized

The lesson from `platform/evaluation-observability` this stage exists to
implement, not just cite: an agent benchmark score is a function of
`(model, tools, system prompt, loop/retry design, context-management policy,
sampling parameters, environment version)`, and disclosing only the model
name discloses the smallest part of what produced the number.
`core/evaluate.py agent-report`'s `REQUIRED_HARNESS_FIELDS` — `tools`,
`max_steps`, `context_budget_tokens`, `model_endpoint`, `temperature`,
`harness_version`, `seed` — is that argument as a validation check rather
than a paragraph: a transcript missing any of them makes the script raise
instead of summarizing. This is the same discipline inspect-ai (UK AISI)
builds a framework around — dataset + solver + scorer, every run logging a
full transcript so disclosure is a byproduct of how the run was recorded
rather than added after the fact. This stage hand-rolls the same idea at the
scale one mission needs, rather than adopting the framework, because the
transcript schema here is this mission's own (see the module docstring).

## What a standard harness gives you, and where it stops

`prod/lm_eval.py` runs the same checkpoint through EleutherAI's
lm-evaluation-harness. What that buys over a hand-rolled loop: task
definitions are declarative (dataset + prompt template + scoring rule — exact
match, or log-likelihood comparison for multiple choice), which is what makes
it possible to run hundreds of community-maintained static benchmarks by
writing one model adapter (`SpeedrunLM` here) instead of one scoring function
per benchmark, with results directly comparable to every other model run
through the same harness version and task revision. Where it stops,
structurally, not as a missing feature: it scores one static task at a time —
a fixed prompt in, a score out — with no notion of a multi-turn trajectory,
no tool calls, no environment state that changes between steps. Running a
checkpoint through lm-eval-harness establishes nothing about how it behaves
as an agent; that half is what `core/evaluate.py agent-report` exists for,
and the two stay separate tools because "static benchmark" and "agentic
trajectory" are different measurement problems, not the same one at a
different scale.

## What this mission's evaluation does NOT prove

Straight from `mission.yaml`'s `does_not_prove`, restated for this stage:

- **No business outcome.** The mission's own stated baseline is a hosted
  frontier model, which will outperform this speedrun's 88M-parameter
  checkpoint on essentially every task — there is no stakeholder metric, no
  live users, and no baseline this beats on output quality. A passing
  perplexity, task-suite, or agent number here is not a claim that this
  system is *good*; it is a claim that the pipeline producing it is real and
  its numbers are honestly reported.
- **No generalization beyond text.** Nothing here says the platform layers
  it exercises (serving, agent harness, eval discipline) work for a
  different modality or decision loop — that claim belongs to a later
  mission that has to re-earn it.
- **No agent-benchmark comparability to anyone else's number**, per the
  harness-disclosure argument, unless that number discloses an identical
  configuration — which most published numbers do not.
- **No task-suite accuracy meaningful outside this repo.** The suite is
  sized for what an 88M from-scratch model can plausibly attempt; it is not
  a capability benchmark.

## Reproducing

```bash
# perplexity — tokenizer identity and context length always land in the report
python core/evaluate.py perplexity --ckpt ../02-pretrain/ckpt/ckpt.pt \
    --tokenizer ../01-tokenizer/tokenizer_hf.json --data ../02-pretrain/data/tokens/val.bin \
    --context-length 1024 --baseline-name "<name>" --baseline-value "<value>" \
    --baseline-source "<where from>" --out runs/perplexity-report.json

# task suite — --seeds is mandatory once the suite has any sampled task
python core/evaluate.py tasks --ckpt ../02-pretrain/ckpt/ckpt.pt \
    --tokenizer ../01-tokenizer/tokenizer_hf.json --suite tasks.jsonl --seeds 5 \
    --baseline-name "<name>" --baseline-value "<value>" --baseline-source "<where from>" \
    --out runs/task-suite-report.json

# agent report — aggregates stage 06's harness-disclosed transcripts
python core/evaluate.py agent-report --transcripts ../06-agent/runs/transcripts/ \
    --baseline-name "<name>" --baseline-value "<value>" --baseline-source "<where from>" \
    --out runs/agent-report.json

# the same checkpoint through the standard static-benchmark harness
python prod/lm_eval.py --ckpt ../02-pretrain/ckpt/ckpt.pt \
    --tokenizer ../01-tokenizer/tokenizer_hf.json --tasks lambada_openai --limit 200 \
    --out lm_eval_report.json
```

[Stage 02](../02-pretrain/) has landed a checkpoint and
[stage 03](../03-sft/) has fine-tuned it, so the commands above now have
something to point at — but none of them has been run, and this README
therefore still reports no perplexity, accuracy, or agent score. That is
deliberate: publishing a number before it exists is exactly the failure mode
this stage argues against, and having a checkpoint available makes the
temptation stronger rather than weaker.

## Exercises

1. **Break the tokenizer-disclosure check.** Run `perplexity` with two
   different tokenizers on the same held-out data; confirm the perplexities
   differ for reasons unrelated to model quality, and explain why the sha256
   sits right next to the number.
2. **Force the single-seed refusal.** Build a `tasks.jsonl` with one
   `generate` instance and run `tasks` without `--seeds`. Read the error,
   then re-run with `--seeds 3` and confirm `per_seed_accuracy` actually
   varies rather than repeating one value three times.
3. **Corrupt a harness-disclosure field.** Delete `temperature` from one
   transcript's `harness` block in an otherwise-valid transcript directory;
   confirm `agent-report` raises rather than silently dropping it.
4. **Compute the bootstrap CI by hand.** Take five `loglik` correctness
   values, resample 2,000 times with `bootstrap_ci`, and compare the interval
   width to a 300-sample, 50%-success-rate example (~±5.7 points) — confirm
   yours is wider, and explain why it should be at n=5.
5. **Compare a real SWE-bench Verified score against SWE-bench Pro's stated
   design.** Find one paper quoting each for the same model family and write
   two sentences on what the second benchmark specifically changes about the
   first's contamination risk.

## What a passing mission report must contain

Per `mission.yaml`'s acceptance criteria, the report this stage produces once
every earlier stage has a verified run must show, per `runs/` entry: the
exact evaluation command and CLI arguments (including the named baseline);
for perplexity, the tokenizer sha256 and context length; for the task suite,
the seed count and per-seed results, not just the mean; for the agent eval,
the harness configuration and confirmation that `harness_configs_seen == 1`
(or a note on which per-transcript harness each number belongs to); and, for
every metric, the `caveats` block this stage's tooling attaches
automatically. A report missing any of these isn't a smaller version of a
passing report — it's a different, weaker claim wearing the same percentage
sign.
