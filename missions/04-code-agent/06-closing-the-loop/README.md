---
status: draft
level: applied
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
attempts were unresolved-and-not-a-timeout).

<!-- RESULTS_TABLE -->

## Verdict

<!-- VERDICT -->

## Cost

<!-- COST -->

## Run it

```bash
cd missions/04-code-agent/06-closing-the-loop/core
uv run python close_the_loop.py \
  --ceiling 30 --already-spent <cumulative-before-this-stage> \
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
reported as no result, exactly as stage 01 and 05 both already do.
