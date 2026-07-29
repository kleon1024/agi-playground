---
status: draft
level: applied
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
lm-evaluation-harness, via a from-scratch adapter. What that buys, and the
class of task it structurally cannot express, is in
[whose harness produced it](whose-harness/).

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

## Three ways a correct number is still false

Everything above makes a score *reproducible*: the tokenizer is named, the
context length is named, the baseline is named, the seed count is enforced.
None of it makes the score *true*. A benchmark whose answers leaked into
training data, an LLM judge with reproducible preferences, and a difference
smaller than the run-to-run noise all produce numbers that pass every check on
this page.

[Why believe the number?](why-believe-the-number/) takes those three in turn,
and states what each defense cannot do. Read it before quoting anything from
this stage — including anything you quote from someone else.

## The other half of the number

Everything above is about the score. The harness that produced it is the other
half, and it is the half nobody names.
[Whose harness produced it](whose-harness/) turns the disclosure argument into
a validation check that raises on a missing field, and answers the tooling
question this stage has to make: EleutherAI's lm-evaluation-harness for static
benchmarks, a hand-rolled loop for agentic trajectories, and why those cannot
be the same tool.

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
2. **Corrupt a harness-disclosure field.** Delete `temperature` from one
   transcript's `harness` block in an otherwise-valid transcript directory;
   confirm `agent-report` raises rather than silently dropping it.

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

## Next

This is the last stage. The mission is complete when every stage above has a
run record and this one produces a report that satisfies the criteria just
listed — not before, which is why several stages are still `draft`.

Two directions from here, and they are different kinds of work:

- **[Why believe the number?](why-believe-the-number/)** — the companion to
  this chapter, and the one to read before quoting anything produced here.
  Contamination, judge bias, and differences smaller than the noise all
  survive every check on this page.
- **[Mission 02 — personalized discovery](../../02-personalized-discovery/)** —
  a different decision loop entirely. This mission proved the language-model
  layers compose; it proved nothing about whether they generalize when the
  objective, data, and failure modes change. That claim has to be re-earned,
  which is what mission 02 exists to attempt.
