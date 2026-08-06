---
status: verified
level: applied
verified: 2026-08-03
label: Closing the loop
---

# Does showing a model the real outcome of its own failed attempt help it fix the bug?

**Before this:** [stage 01](../01-no-harness/) gave the model one blind call --
issue, failing test, source file, produce a diff, applied blind, no retry, no
tools. [Stage 03](../03-cheap-or-expensive/) gave it up to 25 turns with
`Read`, `Bash`, and real test execution. [Stage 04](../04-how-it-fails/)
catalogued what stage 01's twelve unresolved attempts actually did: eleven
diffs `git apply` rejected outright, one diff applied but left the target test
failing, and none of the twelve ever saw that outcome before this stage.

That gap is real and unmeasured: everything between "zero feedback" and "a
full tool loop." This stage isolates the single narrowest slice of it --
outcome-feedback with no tools at all -- and reports what happened.

## Why this question, not a different one

Post-training research has been moving past preference-only optimization
(RLHF: Ouyang et al. 2022, *Training language models to follow instructions
with human feedback*) toward methods that let a model revise its own output
against something it actually produced. Reflexion (Shinn et al. 2023,
NeurIPS, arXiv:2303.11366) has an agent verbally reflect on its own trial's
outcome and retry; Self-Refine (Madaan et al. 2023, NeurIPS, arXiv:2303.17651)
has a model iteratively critique and rewrite its own output using feedback it
generates; RLEF (Gehring et al. 2024, arXiv:2410.02089) grounds a code model
directly in execution feedback -- real compiler and test output -- rather
than a learned or human preference signal. The throughline across all three:
the signal that improves the next attempt is something that actually
happened, not a curated judgment of what a better answer would look like.

This stage does not implement any of those methods. It asks the smallest
version of the question they all point at, inside this mission's own harness:
if a model sees the real, concrete result of its own last diff -- not a
critique, not a reward, just what `git apply` or the test suite actually did
-- does a single corrected attempt do better than the first one did? No
training happens here, no policy is updated, and the model gets no tools. The
next turn is still one shot, with one new fact added to the prompt.

## The mechanism

For every stage-01 attempt that did not resolve and was not a timeout (twelve
of stage 01's eighteen attempts -- the two sonnet timeouts on `b81c414`
produced no diff at all, so there is no prior attempt to show back), this
stage:

1. Materializes the exact same pre-patch task tree stage 01 started from.
2. Re-applies the model's own recorded prior diff to that fresh tree with
   `git apply`, for real, to get the actual outcome -- not a paraphrase of
   the JSONL's `verdict` column, but the real `git apply` stderr if it
   rejected the diff, or the real pytest failure output if it applied but
   the target test still failed.
3. Resets the tree back to base state (a wrong diff does not get left
   applied underneath the retry -- the model is asked for one corrected
   diff against the original file, not a second patch stacked on the first).
4. Sends one new `claude -p` call: the same test command and original
   failure text stage 01 showed, the same source file contents, plus the
   prior diff and the real outcome from step 2, asking for one corrected
   diff. Every tool stage 01 denied is still denied --
   `--disallowedTools` passes the identical list. There is no `--resume`
   and no conversation state carried between calls; each retry is a fresh,
   self-contained prompt, which is why the original context is restated
   rather than assumed.
5. Scores the corrected diff with the identical scorer stage 01 and 03 both
   use: applied, run the target test, run the full suite, check for
   regressions and test-file tampering.

## What is reused, and what is new

Reused by direct import, not copied: `no_harness.py`'s `MINER` and `SCORING`
module handles (task materialization, cleanup, instrumented test commands,
`run_and_collect`, `changed_paths`, `score`), its `read_source_context`,
`invoke` (the `claude -p` subprocess call with the same denied-tools list),
`apply_patch`, and `extract_diff`. The `--ceiling`/`--already-spent`
cost-guardrail pattern is the same one stage 01 established.

New in this stage: the retry prompt template; `apply_patch_verbose`, which
mirrors `apply_patch`'s exact two-strip-level `git apply` logic but returns
the real stderr text instead of discarding it, because the retry prompt needs
the actual error, which stage 01 never had a reason to keep; the
candidate-selection logic that reconstructs which of stage 01's saved diff
files belongs to which JSONL record (stage 01's results file does not store
a run index, so it is rebuilt from record order against the manifest's task
order, verified against the real `runs/diffs/` filenames before being relied
on); and the base-state reset between deriving the real outcome and building
the retry prompt.

## Real numbers

`runs/closing-the-loop-results.jsonl` -- twelve real retry attempts, one per
stage-01 attempt eligible for retry (six haiku, three sonnet, three opus; the
count per tier follows directly from how many of each tier's stage-01
attempts were unresolved-and-not-a-timeout). Full command and per-attempt
detail in [`runs/2026-08-03-closing-the-loop.md`](runs/2026-08-03-closing-the-loop.md).

| Model | Retried | Resolved before (stage 01) | Resolved after one retry | Diff even applied |
|---|---|---|---|---|
| haiku | 6 | 0/6 | 0/6 | 0/6 |
| sonnet | 3 | 0/3 | 1/3 | 1/3 |
| opus | 3 | 0/3 | 1/3 | 1/3 |
| **Pooled** | **12** | **0/12** | **2/12** | **2/12** |

("Resolved before" is 0 for every row by construction: these are exactly the
stage-01 attempts that did not resolve, and the two sonnet timeouts are
excluded because they never produced a diff to retry.)

The retry step was fully bimodal in this run: **every attempt that resolved
is exactly the attempt whose corrected diff applied at all.** There is no
case here of a diff applying but the target test still failing -- the
opposite of the split stage 04 found in stage 01's own baseline (eleven
never-applied, one applied-but-wrong). Ten of these twelve retries still
produced a diff `git apply` rejected, essentially the same failure mode
stage 04 catalogued, just measured on the retry step instead of the first
attempt.

## Verdict

A genuine, small, mixed result -- not a clean win, not a clean null.

**Haiku: no effect.** Six retries, zero resolved, same as before. Seeing the
exact `git apply` error text (or, for the one attempt whose prior diff had
applied, the exact still-failing pytest output) did not change haiku's
output in a way that got a diff to apply, let alone fix the bug.

**Sonnet and opus: one flip each, out of three.** Both tiers went from 0/3 to
1/3 resolved on their retried attempts. That is a real, observed change --
a diff that did not apply the first time applied and fixed the bug the
second time, after the model saw the real error. It is also a single flip at
N=3 per tier, and this stage ran each retry once rather than repeating it the
way stage 01 repeated its own baseline three times per task. There is no
per-tier spread to compare this margin against, the way stage 01 could report
"opus's margin sits inside its own run-to-run spread." Reported plainly: this
is a real positive movement at sonnet and opus, and it is too small a sample
to call decisive on its own.

**Pooled, the headline number:** 0/12 to 2/12 across all three tiers combined
-- a real but modest improvement, entirely explained by two diffs that went
from rejected to applying-and-correct, and by nothing else. Outcome-feedback
did not turn any "applies but wrong" case into "resolved" (there were none in
this batch to begin with, on either side), and it did not reduce the rate of
diffs that fail to apply at all in any way large enough to see at this N (10
of 12 still didn't apply, against 11 of 12 in stage 01's original baseline
covering all outcomes, unresolved and resolved together).

## Cost

| Model | Cost this stage |
|---|---|
| haiku | \$0.4852 |
| sonnet | \$1.3057 |
| opus | \$1.2604 |
| **Total this stage** | **\$3.0513** |

Cumulative mission hosted-API spend: **\$17.9547** of the **\$30** ceiling
(stage 03's \$9.12 + stage 01's \$5.1438 + stage 00's public-set run's \$0.6407
+ this stage's \$3.0513). \$12.0453 of headroom remained unused; the ceiling
was never approached.

## Run it

```bash
cd missions/04-code-agent/06-closing-the-loop/core
uv run python close_the_loop.py \
  --ceiling 30 --already-spent 14.9034 \
  --timeout 240 \
  --out ../runs/closing-the-loop-results.jsonl \
  --keep-diffs ../runs/diffs
```

`--out` is also a resume file: candidates already present in it (matched by
model, task, and prior run index) are skipped on a re-run, so an interrupted
batch can continue rather than re-spending on attempts already scored.

## What this does not establish

A single retry turn with outcome-feedback and no tools is not the "learning
from real task attempts, tool-call outcomes, and failures" that the papers
cited above describe. Nothing here updates a model's weights, nothing here
accumulates across more than one retry, and nothing here gives the model a
way to go look at anything beyond what this stage's prompt hands it. This is
a narrow, bounded test of exactly one variable -- does seeing the real
outcome of your own last attempt help, holding tool access at zero -- not a
claim to have built, or even approximated, a production continual-learning
system. Tool access is stage 02/03's question, answered separately and
already fully resolved on this task set (18/18); this stage does not
re-open it and does not combine the two variables. And with two private
tasks and at most six attempts per tier, this stage inherits stage 01's own
small-N caveat: a gap smaller than that tier's own run-to-run spread is
reported as no result, exactly as stage 01 and 05 both already do. Unlike
stage 01, this stage did not repeat each retry multiple times, so it cannot
report a run-to-run spread for the retry step itself the way stage 01 could
for its baseline -- the sonnet and opus 0/3-to-1/3 movements are reported as
real but statistically thin for exactly that reason.

A detour from here: [does seeing the real outcome help — with still no
tools?](does-feedback-help/) — the recorded 12 attempts read as a
comparison: feedback does not raise the resolve rate, it converts the
dominant blind failure (non-applicable patches) into tryable ones, at one
more priced turn per task.

Another detour: [feedback fixed the fix, not the apply](the-bimodal-retry/) — the recorded retry read: applied and resolved coincide perfectly, ten of twelve corrected diffs were still rejected, and haiku's 0/6 is the negative control.
