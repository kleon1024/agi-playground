---
status: draft
level: applied
label: Agentic platform
---

# When an agent says it fixed the bug, what makes that true?

**Question:** a maintainer gets more bug reports than they have hours. An agent
offers to take some. Before handing over a single one, they need to know two
numbers — how often a patch is actually correct, and what each correct patch
costs — and neither is what an agent reports about itself.

**The artifact this topic follows** is one task: a repository at a commit
where a test fails, and a patch that has to make it pass. Everything below is
about what it takes to believe the word "pass".

## Follow one real run

Before the mechanism, the thing itself. This is a real agent run on one of
the mission's tasks — `private-354c352`, a bug that escaped angle brackets
inside inline code. It ran on 2026-08-14 through the mission harness with a
haiku-tier model, and it resolved: 12 trace steps, 7 turns, \$0.44
([full record](agent-loop/runs/2026-08-14-trace-354c352.md)).

<!-- interactive: TraceStepper -->

Watch the rhythm, because the whole topic is this rhythm at different sizes:
the model *decides*, *acts* through a tool, and *observes* the result before
deciding again. The first half of the trace is investigation — read the test,
read the implementation, reproduce the failure. The middle is the edit. The
last four steps are the reason the topic exists: it does not stop at a green
target test, it re-runs the whole file to prove nothing else broke.

That rhythm is what [the blind call](no-harness/) lacks, what
[the loop](agent-loop/) adds, and what [the harness](agent-loop/harness-anatomy/)
protects. Step through it once here; the stages below build it one layer at a
time.

## Why this topic exists

On 2026-07-29 this repository published a serving engine as `status: verified`.
It had been benchmarked, its throughput table was cited by three chapters, and
every decode step in it attended to a single token. The bug made it *faster*,
so nothing in the numbers looked wrong. It was caught only when a later chapter
added an identity check and compared the output against a full recompute.

That is the failure this topic is built around, because an agent scored by a
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
[the ablation ladder](../01-language-model/02-pretrain/architecture-ablations/)
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
[topic 01's agent harness](../01-language-model/agent-harness/) unchanged
except for the tools this task set requires — same inputs, same objective, a
different decision. That reuse is what makes this topic the second consumer
the [admission gate](../reference/standards/mission-contract.md) asks for,
and the harness stays where it was measured rather than moving into a
directory of its own.

## Model lineage

The artifact and its guardrails sit on two lines: code models (Codex,
CodeLlama, DeepSeek-Coder) and honest scoreboards (SWE-bench, test-gaming
guardrails). The [open-source line behind the code agent](lineage.md)
traces both.

## Stages

The topic reads as one spine — model call, harness, platform, production —
with the stages grouped by the plane they build. The evidence boundary
between the two halves is deliberate and visible in the status column.
Stages 00–06 are the *empirical core*: every claim is anchored to recorded
runs on the mission's task sets, from the blind-call baseline to the
resolve-rate/generality split. Stages 07–17 are the *design agenda*: dated
surveys plus mechanism demos that extend the verified core toward a
bounded autonomous delivery stack, and they are draft by design until a
run backs them. The topic is not a claim that a general agentic platform
has been built and validated; it is a verification-first coding harness,
measured, with the missing layers toward full delivery named and
sketched.

### Call

| Stage | Question | Status |
|---|---|---|
| [The task set](task-set/) | what makes a bug report into a scoreable task? | verified |
| [No harness](no-harness/) | is the loop worth anything over one blind call? | verified |

### Intent

| Stage | Question | Status |
|---|---|---|
| [Intent to plan](intent-to-plan/) | a bug report is not a task; what has to happen between them? | draft |

### Harness

| Stage | Question | Status |
|---|---|---|
| [The agent loop](agent-loop/) | what would change your mind about "it passed"? | verified |
| [Harness comparison](harness-comparison/) | every production harness is the same five decisions; where do they differ? | draft |
| [Cheap or expensive](cheap-or-expensive/) | the cheap model resolved everything; should you use it? | verified |
| [Closing the loop](closing-the-loop/) | does seeing your own attempt's real outcome help, with still no tools? | verified |

### Platform capabilities

| Stage | Question | Status |
|---|---|---|
| [Execution environment](execution-environment/) | where does the agent actually run, and what can that place do to it? | draft |
| [Runtime and durability](runtime-and-durability/) | what happens to the task when the machine dies? | draft |
| [Context and memory](context-and-memory/) | what does the agent remember, and how does it get what it forgot? | draft |
| [Tools and protocols](tools-and-protocols/) | how do an agent and a tool agree on a contract? | draft |

### Platform organization

| Stage | Question | Status |
|---|---|---|
| [Orchestration and workflows](orchestration-and-workflows/) | one agent fixed one bug; how do you organize a task that needs twenty? | draft |
| [Control plane and governance](control-plane-and-governance/) | the agent sees a sandbox; who sees the agent? | draft |
| [Agentic infrastructure](agentic-infrastructure/) | under the platform, what does the machine room look like? | draft |
| [Verification and evals](verification-and-evals/) | how does it fail, does it cheat, and what counts as done? | verified |
| [Autonomy and orchestration](autonomy-and-orchestration/) | how much human is left in the loop, and where exactly? | draft |

### Impact and production

| Stage | Question | Status |
|---|---|---|
| [Industry impact](industry-impact/) | the platform works in this repo; does it work in your industry? | draft |
| [Real tasks](real-tasks/) | the platform passed its own tests; what happens on real work? | draft |
| [The report](report/) | what did we actually establish? | verified |

[Stage 00](00-task-set/) has run. It mined this repository's 100 commits down to
4 candidates and admitted **2**, because a task is admitted only if its test
fails before the fix and passes after it. Half the candidates failed that rule,
and the reason they failed — tests that return early and record a pass when the
file they inspect is absent — is the same defect this topic was built to catch,
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
otherwise. That gap is the topic's own thesis pointed at the topic.

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
is the identical failure mode that motivated this topic: a serving engine
published `verified` because its bug made it faster, and nothing in the
resolve-rate-shaped evidence looked wrong.

<!-- interactive: ResolveVsGenerality -->

SWE-bench (Jimenez et al., 2023) established resolve-rate-against-a-held-out-test
as the standard agentic-coding benchmark metric; by 2024 several follow-up
audits had documented exactly this class of gap -- a patch satisfying a test
suite by construction while remaining wrong outside the space that suite
checks. Stage 03 is this repository's own from-scratch instance of that same
finding.

Per [the mission contract](../reference/standards/mission-contract.md), the contract
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
real attempts this topic has now run. [Stage 05](05-report/) holds all of it
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

The frontier reading is not a stage of its own; it is distributed into the
stage whose decision each chapter changes. The same loop — retry, grounding,
verification, permission ladders, gates — is what every agentic surface that
transacts now runs on, and each frontier chapter returns a decision on top of
the recorded runs, sitting beside the stage that supplies its evidence. The
intent chapter (under [stage 05](05-report/)) reads the produced-vs-delivered
gap (4/18 blind vs 18/18 harness); the anatomy chapter (under
[stage 02](02-agent-loop/)) audits the loop's control and compute planes and
reads Claude Code, Codex, and Antigravity as the same five decisions; the
governance and adversary chapters (under [stage 04](04-how-it-fails/)) price
a reconciliation gate (14/18 blind calls rejected before delivery, zero
tampering across 54 real model calls) and read the guardrail's decision
boundary against its zero-firing real record; and the product chapter (under
[stage 03](03-cheap-or-expensive/)) draws the automate-versus-gate line as a
routing table priced per delivered outcome. No model was called and no new
run was executed to produce them — every number traces to this mission's
`runs/` entries or to a dated external source.

<!-- interactive: AgentFrontier -->



## Where each stage leaves the path

A stage states a decision; these deep-dive chapters answer the decisions
the main path asserts without showing, topic-01 style — each returns an
artifact or a measurement the next stage consumes.

| At this stage | You need to decide | So read |
|---|---|---|
| `00-task-set` | The yield is the finding | [the-two-of-six-yield](00-task-set/the-two-of-six-yield/) |
| `00-task-set` | What does the mined task set actually contain? | [what-the-task-set-contains](00-task-set/what-the-task-set-contains/) |
| `01-no-harness` | The blind call, read: what one attempt without a loop costs | [when-the-blind-call-fails](01-no-harness/when-the-blind-call-fails/) |
| `01-no-harness` | The first gate a blind call must pass | [when-the-patch-does-not-apply](01-no-harness/when-the-patch-does-not-apply/) |
| `02-agent-loop` | The harness, drawn as its steps and checks | [the-loop-that-scores-a-patch](02-agent-loop/the-loop-that-scores-a-patch/) |
| `02-agent-loop` | When does the test-file guardrail refuse a patch? | [when-the-guardrail-refuses](02-agent-loop/when-the-guardrail-refuses/) |
| `02-agent-loop` | What does the software around the model own? | [harness-anatomy](02-agent-loop/harness-anatomy/) |
| `03-cheap-or-expensive` | The expensive tier is not the fastest | [the-cost-quality-knee](03-cheap-or-expensive/the-cost-quality-knee/) |
| `03-cheap-or-expensive` | When every tier resolves everything, which tier won? | [the-tier-that-won](03-cheap-or-expensive/the-tier-that-won/) |
| `03-cheap-or-expensive` | When should the agent act, and when should a human sign it? | [what-a-reasonable-agentic-product-is](03-cheap-or-expensive/what-a-reasonable-agentic-product-is/) |
| `04-how-it-fails` | Zero failures is a real result, not a gap | [the-zero-failure-taxonomy](04-how-it-fails/the-zero-failure-taxonomy/) |
| `04-how-it-fails` | When the patch cannot even be applied, what is the loop buying? | [when-the-patch-cannot-apply](04-how-it-fails/when-the-patch-cannot-apply/) |
| `04-how-it-fails` | What does a governed agent actually do? | [control-plane-governance](04-how-it-fails/control-plane-governance/) |
| `04-how-it-fails` | When is the agent the action? | [the-agent-is-the-action](04-how-it-fails/the-agent-is-the-action/) |
| `04-how-it-fails` | What does the adversary that adapts change? | [the-adversary-that-adapts](04-how-it-fails/the-adversary-that-adapts/) |
| `05-report` | The 6/6 that says nothing about the 18/18 | [the-public-set-control](05-report/the-public-set-control/) |
| `05-report` | The PARTIAL, read bullet by bullet | [when-the-partial-verdict](05-report/when-the-partial-verdict/) |
| `05-report` | Where does intent stop being delivered? | [intent-to-delivery](05-report/intent-to-delivery/) |
| `06-closing-the-loop` | Does seeing the real outcome help — with still no tools? | [does-feedback-help](06-closing-the-loop/does-feedback-help/) |
| `06-closing-the-loop` | Feedback fixed the fix, not the apply | [the-bimodal-retry](06-closing-the-loop/the-bimodal-retry/) |

## Landscape surveys

Dated research passes on the agent-harness and inference-infrastructure
options the stages compare. Reference material, not part of the reading
order.

- [Agent memory — landscape survey](agent-memory-landscape/)
- [Inference and agent-harness infrastructure — landscape survey](infra-agent-harness-landscape/)

## What this will not prove

Every task arrives with a reproducing test already written. That is the
selection that makes the benchmark tractable and also its largest distortion:
writing the test is usually the hard part of a bug report, and this topic
hands the agent that work for free. Full boundary in
[`mission.yaml`](mission.yaml) under `does_not_prove`.

## Toward full delivery: what the verified core does not cover

The verified core (stages 00–06) proves the harness loop and its economics
on bug-fixing tasks with known answers. Moving from that to *autonomous
end-to-end delivery* — a signal in, a validated outcome out — requires six
layers the task set never exercises, and each is a named gap rather than
an aspiration:

1. **Objective and decision rights** — the intent layer must carry utility,
   priority, and who owns each call, not just constraints
   ([intent-to-plan](intent-to-plan/)). "Why" survives as the replanning
   function.
2. **Domain model and system of record** — the agent must know what entity
   the world holds and which store is authoritative, or every action is a
   guess about state.
3. **Distributed side-effect semantics** — at-least-once execution demands
   idempotency keys, outboxes, and compensation
   ([runtime-and-durability](runtime-and-durability/)).
4. **Security and trust boundaries** — prompt injection, tool-output
   poisoning, and provenance, not just a sandbox
   ([execution-environment](execution-environment/),
   [control-plane-and-governance](control-plane-and-governance/)).
5. **Economics of autonomy** — cost per *verified outcome* and human review
   minutes, not cost per attempt
   ([cheap-or-expensive](cheap-or-expensive/)).
6. **Bounded recursive improvement** — the system may propose changes to
   itself, but evaluation, deployment authority, and rollback must live
   outside its reach
   ([closing-the-loop](closing-the-loop/)).

The honest position of this topic: the empirical core proves the loop;
these six layers are the agenda that would turn the loop into a delivery
stack. Each is a future stage with its own mission contract, not a claim
already measured here.
