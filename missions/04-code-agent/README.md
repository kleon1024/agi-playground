---
status: draft
label: Code agent
---

# When an agent says it fixed the bug, what makes that true?

**Question:** a maintainer gets more bug reports than they have hours. An agent
offers to take some. Before handing over a single one, they need to know two
numbers — how often a patch is actually correct, and what each correct patch
costs — and neither is what an agent reports about itself.

**The artifact this mission follows** is one task: a repository at a commit
where a test fails, and a patch that has to make it pass. Everything below is
about what it takes to believe the word "pass".

## Why this mission exists

On 2026-07-29 this repository published a serving engine as `status: verified`.
It had been benchmarked, its throughput table was cited by three chapters, and
every decode step in it attended to a single token. The bug made it *faster*,
so nothing in the numbers looked wrong. It was caught only when a later chapter
added an identity check and compared the output against a full recompute.

That is the failure this mission is built around, because an agent scored by a
test suite has a much shorter path to it. A model that cannot satisfy an
assertion can delete the assertion, and a scoreboard reading 100% is exactly
what that looks like from outside. So the guardrail is not a line in the system
prompt asking the agent to behave. It is a check on the diff, and a patch that
touches a test file is scored as a failure and written into the record.

## What gets measured

Two baselines, because each answers a question the other cannot.

**No harness** is one model call: here is the issue, here is the failing test,
produce a patch, applied blind. No tools, no test feedback, no second attempt.
This is the control that decides whether the loop is worth building at all — if
a full agent harness cannot beat a single call, the harness is decoration.

**Always-frontier** routes every task to the expensive model. It is hard to
beat on resolve rate and easy to beat on cost, which is why the metric is a
pair: **resolve rate** — the target test passes *and* nothing that passed
before now fails — reported beside **dollars per resolved task**. Cost per
*attempt* flatters whichever model fails fastest, so it is not the number the
maintainer's decision turns on.

Both are measured against a locally-served open-weights model and a hosted
frontier model, over at least three runs each. Agent runs are non-deterministic;
[mission 02](../02-personalized-discovery/) already established that a single
seed is not a result, and
[the ablation ladder](../../platform/training/02-architecture-ablations/)
established what to do when a gap is smaller than the spread — report no result.

## Two task sets, never pooled

The public set gives comparability. The private set gives a contamination
control: tasks mined from this repository's own git history, where a fix commit
touched both code and tests, reverted so that the test fails again. The
causal-masking fix above is one of them, and it is a genuinely hard instance.

Scores are reported separately and never averaged together. One set may be in
the training data of every model tested; the other provably is not. Pooling
them would hide the only comparison that says which is which.

## Status

`mission.yaml` is written and committed. Nothing else here has run, so nothing
here reports a number. Per
[the mission contract](../../standards/mission-contract.md), the contract is
declared before the system is built, so that the baseline and the metric cannot
be chosen after seeing which ones flatter the result.

## What this will not prove

Every task arrives with a reproducing test already written. That is the
selection that makes the benchmark tractable and also its largest distortion:
writing the test is usually the hard part of a bug report, and this mission
hands the agent that work for free. Full boundary in
[`mission.yaml`](mission.yaml) under `does_not_prove`.
