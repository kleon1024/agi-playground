---
status: verified
level: applied
base: scratch
verified: 2026-07-30
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

1. **Which harness, exactly?** Beyond a single forward pass — any agent, any
   multi-turn task — the score is a function of (model, tool schemas, system
   prompt, loop/retry design, context-management policy, sampling
   parameters, environment version), and most published numbers disclose
   only the first. This stage's track is named after the 2026 paper *"Stop
   Comparing LLM Agents Without Disclosing the Harness"*: two papers
   reporting "Model A beats Model B" under different scaffolds aren't making
   a comparable claim.
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

Everything above makes a score *reproducible* — tokenizer, context length,
baseline, and seed count are all named or enforced — not *true*. A leaked
benchmark, a judge with reproducible preferences, and a difference smaller
than run-to-run noise all pass every check on this page.

[Why believe the number?](why-believe-the-number/) takes those three in turn and
states what each defense cannot do. Read it before quoting anything from this
stage — including anything you quote from someone else.

## The other half of the number

Everything above is about the score. The harness that produced it is the
other half — in one published 2026 result, worth three times the score with
the model unchanged. [Whose harness produced it](whose-harness/) separates
harness properties with a right answer from ones that are only *declared*,
and settles this stage's tooling question: lm-evaluation-harness for static
benchmarks, a hand-rolled loop for agentic trajectories.

## What this mission's evaluation does NOT prove

Straight from `mission.yaml`'s `does_not_prove`, restated for this stage:

- **No business outcome.** The mission's baseline is a hosted frontier model
  that outperforms this 88M checkpoint on nearly every task — there is no
  stakeholder metric or live-user baseline. A passing number here claims the
  pipeline is real and honestly reported, not that the system is *good*.
- **No generalization beyond text.** Nothing here says the platform layers
  it exercises work for a different modality or decision loop — that claim
  belongs to a later mission.
- **No agent-benchmark comparability to anyone else's number**, per the
  harness-disclosure argument, unless it discloses an identical
  configuration.
- **No task-suite accuracy meaningful outside this repo.** The suite is
  sized for what an 88M from-scratch model can plausibly attempt; it is not
  a capability benchmark.

## What the perplexity report actually says

Run against stage 02's checkpoint and its held-out `val.bin`:

```
checkpoint   stage02/ckpt/ckpt.pt  (sha256 ffd32ce920c4...)
tokenizer    stage01/tokenizer.json  (sha256 0b2ce230b496...)
context      1024 tokens, stride 1024
windows      4882
perplexity   21.677  (mean NLL 3.0762 +/- 0.3214)
baseline     uniform distribution over vocab = 9.712 nats (ln(16512))
```

Full report: [`runs/2026-07-30-perplexity-report.json`](runs/2026-07-30-perplexity-report.json).

## What the task-suite report actually says

[`fixtures/tasks.jsonl`](fixtures/tasks.jsonl): 8 `loglik` instances (three-way
multiple choice) and 4 `generate` instances, run against the SFT checkpoint at
5 seeds:

```
loglik      accuracy 0.625 (5/8)  95% CI [0.250, 0.875]  bootstrap, n=8
generate    mean 0.050 +/- 0.100 across 5 seeds  [0.0, 0.0, 0.0, 0.25, 0.0]
baseline    random choice among 3 options = 0.333
```

Loglik beats chance, but the CI spans half the range at n=8 — barely more
than "probably better than random." Generate is the harder test: it must
reproduce an exact prefix at temperature 0.8, which an 88M model rarely does
even when loglik ranks the right answer highest. The two disagree because
they measure different things, not because one is wrong.

Full report: [`runs/2026-07-30-task-suite-report.json`](runs/2026-07-30-task-suite-report.json).

## What the agent report actually says

Aggregated from stage 06's six real transcripts:

```
transcripts  6 across 2 tasks, 1 harness config
count-py-files          success 0.00  (3 rollouts, 6.0 steps avg)
find-resolve-in-jail    success 0.00  (3 rollouts, 6.0 steps avg)
overall                 0.000  95% CI [0.000, 0.000]
baseline                chance = 0.0 (no ReAct examples in this checkpoint's SFT mix)
```

`harness_configs_seen == 1`, so all six rollouts are comparable. Zero success
is itself the finding: [stage 06's own
run](../06-agent/runs/2026-07-30-real-agent-run.md) traces it to a
format-following failure, not a reasoning one — the model never emitted one
parseable `Action:` line to even fail at executing.

Full report: [`runs/2026-07-30-agent-report.json`](runs/2026-07-30-agent-report.json).

## The fix and its trade

The failure is a number-shaped object: "68% on benchmark X" is missing
the tokenizer and context length, the harness, the seed count, and the
baseline, and each omission independently makes the number impossible to
compare. The fix is a report format that refuses to emit the claim when
the disclosure is missing — `perplexity` writes the tokenizer's sha256
and exact context length beside every number; `tasks` raises on
`--seeds 1`; every subcommand calls `require_baseline()`; and
`agent-report` raises when a transcript's `harness` block lacks any
field or a task has fewer than three rollouts. The trade is measured by
the reports the script does emit. The refusal costs nothing to compute
but costs the convenient sentence: the loglik report's 0.625 (5/8)
carries a bootstrap CI of [0.250, 0.875] at n=8 — barely more than
"probably better than random" against the 0.333 baseline — and the
generate report's mean 0.050 plus or minus 0.100 across five seeds
([0.0, 0.0, 0.0, 0.25, 0.0]) is the honest version of "it worked." The
agent report's 0.000 with CI [0.000, 0.000] across six transcripts and
one harness config is the same discipline applied to a negative result:
zero success is itself the finding, and the report says why
(format-following failure, not reasoning). Perplexity at context 1024
(21.677, mean NLL 3.0762 plus or minus 0.3214, against the uniform
baseline of 9.712 nats) is only comparable to itself — the same number
at a different context length or tokenizer is a different claim.

## Who owns the loop

The honest-number discipline only survives if each owner holds one
piece:

- **The evaluation and measurement team** owns the report format and the
  refusal: the mandatory seed count, the named baseline, and the
  `does not prove` section. It owns the underpowered-N failure — the n=8
  CI that spans half the range is this team's job to report, not to
  smooth over.
- **The harness owner** owns the `harness` disclosure block: the agent
  score is a function of tools, loop, retries, and sampling parameters,
  and `harness_configs_seen == 1` is the check that six rollouts are
  actually comparable. It owns the undisclosed-harness failure this
  stage's track is named after.
- **The data team** owns the contamination and leakage that pass every
  check on this page ([why believe the number](why-believe-the-number/)):
  a leaked benchmark, a judge with reproducible preferences, and a
  difference smaller than run-to-run noise all survive a fully disclosed
  report.
- **The product and release owner** owns the ship/reject decision on top
  of the number ([who decides to ship](who-decides-to-ship/)): the
  report proves the pipeline is real and honestly reported, never that
  the system is good.

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

[Stage 02](../02-pretrain/) landed a checkpoint, [stage 03](../03-sft/)
fine-tuned it, and [stage 06](../06-agent/) ran it through the harness.
Perplexity, the task suite, and the agent report are all measured, above —
the honest-reporting discipline this stage argues for, applied to itself.

## Exercises

1. **Break the tokenizer-disclosure check.** Run `perplexity` with two
   different tokenizers on the same held-out data; confirm the perplexities
   differ for reasons unrelated to model quality, and explain why the sha256
   sits right next to the number.
2. **Corrupt a harness-disclosure field.** Delete `temperature` from one
   transcript's `harness` block in an otherwise-valid transcript directory;
   confirm `agent-report` raises rather than silently dropping it.

## What a passing mission report must contain

Per `mission.yaml`'s acceptance criteria, the report this stage produces must
show, per `runs/` entry: the exact command and CLI arguments including the
named baseline; tokenizer
sha256 and context length for perplexity; seed count and per-seed results
(not just the mean) for the task suite; harness configuration and
`harness_configs_seen == 1` for the agent eval; and the `caveats` block for
every metric. A report missing any of these is a different, weaker claim
wearing the same percentage sign.

## Next

This is the last stage. The mission is complete when every stage above has a
run record and this one produces a report that satisfies the criteria just
listed — not before, which is why several stages are still `draft`.

Two directions from here, and they are different kinds of work:

- **[Why believe the number?](why-believe-the-number/)** — the companion to
  this chapter, and the one to read before quoting anything produced here.
  Contamination, judge bias, and differences smaller than the noise all
  survive every check on this page. When the question is specifically whether
  a gap is larger than the noise,
  [is a difference significant?](../../foundations/06-significance/) is the
  arithmetic, and [who decides to ship](who-decides-to-ship/) is what a release
  decision needs on top of the number.
- **[Mission 02 — personalized discovery](../../02-personalized-discovery/)** —
  a different decision loop entirely. This mission proved the language-model
  layers compose; it proved nothing about whether they generalize when the
  objective, data, and failure modes change. That claim has to be re-earned,
  which is what mission 02 exists to attempt.
