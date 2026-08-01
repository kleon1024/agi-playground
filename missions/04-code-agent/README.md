---
status: draft
level: applied
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

## Stages

| Stage | Question | Status |
|---|---|---|
| [00 — The task set](00-task-set/) | what makes a bug report into a scoreable task? | verified |
| 01 — No harness | is the loop worth anything over one blind call? | not started |
| [02 — Scoring the attempt](02-agent-loop/) | what would change your mind about "it passed"? | verified |
| [03 — Cheap or expensive](03-cheap-or-expensive/) | the cheap model resolved everything; should you use it? | verified |
| 04 — How it fails | how does it fail, and does it cheat? | not started |
| 05 — The report | what did we actually establish? | not started |

[Stage 00](00-task-set/) has run. It mined this repository's 100 commits down to
4 candidates and admitted **2**, because a task is admitted only if its test
fails before the fix and passes after it. Half the candidates failed that rule,
and the reason they failed — tests that return early and record a pass when the
file they inspect is absent — is the same defect this mission was built to catch,
found in our own suite by the rule that mines it.

[Stage 02](02-agent-loop/) has run the full path end to end — materialize,
baseline, agent loop, diff, score — driven by scripted backends rather than a
model, and the test-tampering guardrail is demonstrated firing on a patch whose
every other signal reads as a clean fix.

[Stage 03](03-cheap-or-expensive/) put three model tiers through the task set,
three runs each. All eighteen attempts resolved, at $0.16 per resolved task on
the cheapest tier against $0.82 on the most expensive — and reading the patches
showed the cheapest tier had produced three latent defects the resolve rate
cannot see. The primary metric says route everything cheap; the diffs say
otherwise. That gap is the mission's own thesis pointed at the mission.

Concretely: stage 03's real run resolved all 18 attempts across three model
tiers (haiku, sonnet, opus -- 6 each), so `resolve_rate = 18/18` is identical
across every tier and tells a reader nothing about which tier to pick.
`probe_generality.py` re-checks each patch against a 4-token query on a live
6-token cache, at the same 2e-5 tolerance the target test uses. Haiku's
patches diverge by 1.2e-3 to 4.2e-2 against a correct-patch baseline of
5.960e-08 -- three orders of magnitude off, on all three of its runs. Sonnet
and opus hold tolerance on all three of theirs. `resolve_rate = 18/18` and
`patch_generality = 6/9` are both true and measure different claims: "passes
the given test" versus "correct outside the shape the test exercises." This
is the identical failure mode that motivated this mission: a serving engine
published `verified` because its bug made it faster, and nothing in the
resolve-rate-shaped evidence looked wrong.

<!-- interactive: ResolveVsGenerality -->

SWE-bench (Jimenez et al., 2023) established resolve-rate-against-a-held-out-test
as the standard agentic-coding benchmark metric; by 2024 several follow-up
audits had documented exactly this class of gap -- a patch satisfying a test
suite by construction while remaining wrong outside the space that suite
checks. Stage 03 is this repository's own from-scratch instance of that same
finding.

Per [the mission contract](../../reference/standards/mission-contract.md), the contract
was declared before the system was built, so the baseline and the metric cannot
be chosen after seeing which ones flatter the result. The no-harness baseline
in stage 01 has not run, so the value of the loop itself is still unmeasured.

## What this will not prove

Every task arrives with a reproducing test already written. That is the
selection that makes the benchmark tractable and also its largest distortion:
writing the test is usually the hard part of a bug report, and this mission
hands the agent that work for free. Full boundary in
[`mission.yaml`](mission.yaml) under `does_not_prove`.
