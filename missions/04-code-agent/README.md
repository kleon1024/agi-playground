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
[the ablation ladder](../../missions/01-language-model-agent/02-pretrain/architecture-ablations/)
established what to do when a gap is smaller than the spread — report no result.

## Two task sets, never pooled

The public set gives comparability. The private set gives a contamination
control: tasks mined from this repository's own git history, where a fix commit
touched both code and tests, reverted so that the test fails again. The
causal-masking fix above is one of them, and it is a genuinely hard instance.

Scores are reported separately and never averaged together. One set may be in
the training data of every model tested; the other provably is not. Pooling
them would hide the only comparison that says which is which.

## What this reuses

The loop, tool schemas, permission ladder, and stop conditions come from
[mission 01's agent harness](../01-language-model-agent/06-agent/) unchanged
except for the tools this task set requires — same inputs, same objective, a
different decision. That reuse is what makes this mission the second consumer
the [admission gate](../../reference/standards/mission-contract.md) asks for,
and the harness stays where it was measured rather than moving into a
directory of its own.

## Model lineage

The artifact and its guardrails sit on two lines: code models (Codex,
CodeLlama, DeepSeek-Coder) and honest scoreboards (SWE-bench, test-gaming
guardrails). The [open-source line behind the code agent](../../reference/research/lineages/04-code-agent.md)
traces both.

## Stages

| Stage | Question | Status |
|---|---|---|
| [00 — The task set](00-task-set/) | what makes a bug report into a scoreable task? | verified |
| [01 — No harness](01-no-harness/) | is the loop worth anything over one blind call? | verified |
| [02 — Scoring the attempt](02-agent-loop/) | what would change your mind about "it passed"? | verified |
| [03 — Cheap or expensive](03-cheap-or-expensive/) | the cheap model resolved everything; should you use it? | verified |
| [04 — How it fails](04-how-it-fails/) | how does it fail, and does it cheat? | verified |
| [05 — The report](05-report/) | what did we actually establish? | verified |
| [06 — Closing the loop](06-closing-the-loop/) | does seeing your own attempt's real outcome help, with still no tools? | verified |

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
three runs each. All eighteen attempts resolved, at \$0.16 per resolved task on
the cheapest tier against \$0.82 on the most expensive — and reading the patches
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
be chosen after seeing which ones flatter the result.

[Stage 01](01-no-harness/) has since run the no-harness control: one blind
`claude -p` call per attempt, every tool denied, a diff applied blind with no
retry. Resolve rate came back 0/6 (haiku), 1/6 (sonnet), 3/6 (opus) against the
harness's 6/6 on every tier — decisive at haiku and sonnet, and a genuine no
result at opus, where the margin sits inside that arm's own run-to-run spread
at this task set's N=2. [Stage 04](04-how-it-fails/) then catalogued every real
failure across both arms: eleven of stage 01's twelve unresolved attempts never
produced a diff `git apply` would even accept, and the test-tampering guardrail
has still never fired on a real model attempt, in either arm, across all 36
real attempts this mission has now run. [Stage 05](05-report/) holds all of it
against `mission.yaml` mechanically and initially found five of seven
acceptance bullets met — the other two undecidable, both because stage 00
mined only a private task set and never built the public companion
`mission.yaml` calls for, not because anything resolved worse than declared.

[Stage 00](00-task-set/) has since built that companion: two tasks mined from
[more-itertools](https://github.com/more-itertools/more-itertools) (MIT),
using the identical fail-at-base/pass-at-gold rule pointed at a public,
permissively-licensed repository instead of this one. A real haiku run
resolved both, every one of three repeats — 6/6, zero tampering, extending the
"guardrail never fired on a real attempt" finding to 42 real attempts and a
second, previously unseen codebase. Re-running stage 05's report against this
now resolves six of seven bullets MET — the public/private separation bullet
that was undecidable is now MET — and the seventh moves from undecidable to
**PARTIAL**: the harness's own resolve rate on the public set is real (6/6),
but no no-harness control has been run against that set yet, so the "beats
no-harness, both task sets" bullet cannot fully close without it.

[Stage 06](06-closing-the-loop/) has since asked the question sitting between
stage 01's zero feedback and stage 03's full tool loop: for every no-harness
attempt that failed and produced a diff, show the model its own prior diff
plus the real `git apply` error or real test failure it caused, and ask for
one corrected diff -- still no tools. Twelve real retries across the three
tiers: haiku 0/6 resolved (no change), sonnet 1/3, opus 1/3 — pooled 0/12 to
2/12. Both tiers that moved did so on a diff that went from rejected to
applying-and-correct; no attempt in this batch moved from "applies but wrong"
to resolved, and ten of the twelve retries still produced a diff `git apply`
rejected. A real, modest, mixed result, not a clean win.

## What this will not prove

Every task arrives with a reproducing test already written. That is the
selection that makes the benchmark tractable and also its largest distortion:
writing the test is usually the hard part of a bug report, and this mission
hands the agent that work for free. Full boundary in
[`mission.yaml`](mission.yaml) under `does_not_prove`.
