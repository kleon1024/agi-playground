---
status: verified
level: frontier
base: scratch
label: Decomposing a large intent
verified: 2026-08-14
---

# A large intent is not a bigger leaf. How does it become a tree of verifiable work?

**Question:** [stage 02](../) converts a sentence into one task record — one
leaf with one test that decides done. But real work arrives as *"the site's
docs pipeline is broken, the serving engine is wrong, and fix the ordering
too"*: several leaves plus the decision of how they relate. What separates a
large intent from a leaf, and how does a harness turn it into a tree of work
it can actually run?

**The artifact this chapter follows** is the output of
[a rule-based decomposer](core/decomposer.py) run on this mission's real task
records — the tree, the DAG, and the coupling warnings it produces ([record](runs/2026-08-14-decomposer.md)).
The demo is the chapter's spine: every claim below is a line it prints.

**Before this:** [stage 02's constraint-set model](../) — intent as a set of
constraints, of which a task record carries the checkable ones. A large
intent is that model at one level up: the constraint set now spans several
leaves, and satisfying it requires deciding *how they relate*.

## What "large" adds: subgoals and dependencies

A leaf is a constraint set with one done condition. The mission's mined
records are leaves by construction — each carries `source_files`, a
`target_tests` file, and a `test_command` that decides done. Nothing about a
large intent is different in kind; two things appear that a single leaf never
has:

| | Leaf | Large intent |
|---|---|---|
| Done condition | one test command | a set of test commands **plus** a topology |
| Units | none — one task | subgoals (who owns what) |
| Ordering | none — one task | dependencies (what waits for what) |
| Failure | one task fails | tasks conflict, duplicate, or omit work |

The last row is the point. A large intent fails in ways a leaf cannot: two
agents editing the same file, two leaves covering the same requirement, a
requirement covered by no leaf. The decomposition exists to make those three
failures *visible before execution* — which is the same job the plan did for
one leaf, one level up.

## The shape: a tree of ownership over a DAG of dependencies

Two structures appear when an intent grows, and they answer different
questions. The **tree** is ownership: the root is the intent, each subtree is
a subgoal, each leaf is a task with a done condition. The **DAG** is
ordering: an edge says "this must wait for that". A flat list hides both —
it states neither who owns what nor what must wait for what.

The same four sentences from this mission's history read three different ways,
and only one is executable:

```text
The ticket list (what the requester wrote)
  1. fix the serving engine
  2. stop escaping angle brackets in docs
  3. restore the dropped sidebar pages
  4. drop generated numbers from titles

Naive fan-out (what a greedy planner might produce)     Coupling-aware DAG (what the code allows)
                                                       ┌──────────────────────────────┐
  4 agents fan out:                                    │ Lane 1 (independent):        │
  agent A -> engine.py                                   │   b81c414  engine.py         │
  agent B -> sync-docs.py  ── collision ──┐             └──────────────┬───────────────┘
  agent C -> sync-docs.py  ── collision ──┼── same file               │ width 2
  agent D -> sync-docs.py  ── collision ──┘             ┌──────────────┴───────────────┐
                                                       │ Lane 2 (coupled, serial):     │
  Result: three agents write the same file              │ 354c352 → 642074a → be65ef6  │
  in an order nobody chose.                             │ all three touch sync-docs.py │
                                                       └──────────────────────────────┘
```

The decomposition's job is to find the width: how many agents can work
without contending on a file. It is a property of the code, not of the
intent's size — a six-sentence intent can have width 1, and a four-sentence
one can have width 2. This mission's own history shows both extremes, which
is what the demo's runs measure.

## The four invariants

Research and production practice converge on the same four properties a
decomposition must have. Each is checkable, and three of the four are
checkable mechanically:

| Invariant | The question it answers | Mechanical check | In this mission |
|---|---|---|---|
| 1. Leaves independently verifiable | Can a leaf be scored alone? | every leaf has a test + command | satisfied by the mining rule — only fail-at-base/pass-at-gold tasks were admitted |
| 2. Dependencies explicit | Can the runner know the order? | shared files and tests become edges | the decomposer's lanes and coupling flags |
| 3. Collective sufficiency | Does the tree cover the intent? | every intent constraint maps to a leaf and vice versa | needs a constraint list; reviewer's call — the demo says so |
| 4. QA separated from completion | Who checks the split? | the decomposer is not the executor | the demo assigns no lane order and claims no correctness |

Invariant 1 is the 15-minute unit rule from agent-engineering practice: each
unit independently verifiable, a single dominant risk, a clear done condition
([agentic-engineering](https://github.com/marshall0524/everythingclaudecode/blob/main/skills/agentic-engineering/SKILL.md)).
It is also the first thing the mission's mining rule enforces, which is why
every task in [the task set](../../task-set/) passes it by construction.

Invariant 2 is what turns a list into a DAG. Tools that take it seriously
recompute state from the edges: a card in plandeck auto-promotes to *Ready*
only when every `depends_on` card is done, and a dependency cycle is never
marked Ready — it is flagged instead
([plandeck](https://github.com/OthmanAdi/plandeck)). The mission's records do
not carry explicit `depends_on`, so the decomposer derives candidate edges
from the only ground truth it has: file and test overlap.

Invariant 4 is the discipline that production decomposers actually enforce.
The task-decomposer agent in the claude-code-workflows collection is defined
as a *mechanical handoff*: it converts an approved plan into task files,
preserving dependencies, rollback boundaries, and verification "unchanged",
and is explicitly forbidden from introducing new requirements or design
decisions ([task-decomposer](https://github.com/shinpr/claude-code-workflows/blob/main/agents/task-decomposer.md)).
The senacor dev-lead agent goes further: the coordinator is *forbidden from
writing code* — "Parallelism is where the rule is hardest to keep"
([senacor, 2026](https://senacor.blog/introducing-a-dev-lead-agent-a-coordinator-forbidden-from-writing-code-and-why-it-has-to-be/)).
The decomposer and the executor are different roles because a decomposer that
also executes grades its own decomposition.

## The three failure directions, with the cases that prove them

Decompositions fail in three directions, and the failure cases are now
documented with numbers.

**Under-decomposition: a leaf with no done condition.** The unit is too big
to verify — "fix the thing that broke last night" with no test, no budget, no
comparison. The agent then verifies by assertion instead of by test, which is
the failure the mission's guardrails exist to catch. The fix is invariant 1:
refuse the leaf until it carries a machine-checkable done condition.

**Over-decomposition: coordination tax.** Splitting has a real cost — every
spawned agent carries context, prompt, and merge overhead — and it is easy to
pay without earning any parallelism. A single Claude Code workflow invocation
spawned 46 subagents consuming ~3M tokens in ~18 minutes, with the fan-out
cost invisible until it was complete
([claude-code #66023](https://github.com/anthropics/claude-code/issues/66023)).
The counter-example is the marcus snake-game audit: two agents were
configured, one wrote 100% of the product code, and the other produced zero —
the split cost was paid and no parallelism was earned
([marcus #267](https://github.com/lwgray/marcus/issues/267)).

**Wrong-axis decomposition: splitting by intent nouns when the code is
coupled.** This is the most instructive failure, because the cause is
measurable. Marcus split "movement" and "food collection" into separate
tasks; at the code level both live in the same function, `tick()` in
`gameLogic.ts`. One agent did everything. The proposed fix is a *topology
check*: predict each task's files, build a file-overlap matrix, and when any
pair overlaps at least 30%, switch from feature-based to layer-based
decomposition or merge the tasks. The lesson is that the decomposition axis
is decided by the code's coupling, not by the intent's nouns.

This mission's own data reproduces the finding. The demo run on
`candidates.jsonl` ([record](runs/2026-08-14-decomposer.md)) shows the three
site tasks — "stop escaping angle brackets", "restore dropped sidebar pages",
"drop generated numbers" — all touching `site/sync-docs.py` and all targeting
`tests/test_sync_docs.py`. A noun-based split would fan three agents onto one
file, the snake-game failure exactly. The overlap matrix flags it:

| Pair | Overlap | Shared file |
|---|---:|---|
| `354c352` ↔ `642074a` | 0.50 | `site/sync-docs.py` |
| `354c352` ↔ `be65ef6` | 0.50 | `site/sync-docs.py` |
| `642074a` ↔ `be65ef6` | 0.33 | `site/sync-docs.py` |

And the public candidate set is the extreme case: all six tasks touch
`more_itertools/more.py` (pairwise overlap 1.00), so "harden the itertools
library" decomposes to width 1 — one serial lane, not a tree. A large intent
is not a license to fan out; the topology decides.

**Interface drift — the failure that appears only at integration.** Parallel
builders can each finish against their own assumption of an interface, and
the pieces then refuse to integrate. Senacor's dev-lead run hit exactly this
in a multi-repo product: "each builder finishes against its own assumption
of the API and the pieces refuse to integrate". Their fix is contract-first:
the interface contract is authored as part of the plan, committed first to
the contract's repository, and owned by the lead; builders are dispatched in
parallel only against the frozen contract, and a builder that needs to
deviate reports back so the lead updates the contract
([senacor, 2026](https://senacor.blog/introducing-a-dev-lead-agent-a-coordinator-forbidden-from-writing-code-and-why-it-has-to-be/)).
Interface drift is the reason invariant 4 (QA separation) is not a style
choice: the coordinator that owns the contract cannot also be one of the
builders, because then nobody owns the contract.

## Where the decomposition lives: prompt, or control logic?

The deepest structural question is not *how* to decompose but *where* the
decomposition lives. A 2026 study ran three configurations of the same
agentic coding workloads — monolithic prompt, static decomposition with
fixed subtasks, and runtime-structured decomposition where execution flow is
managed by executable control logic and the model is used only for focused
judgment ([arXiv:2605.15425](https://arxiv.org/abs/2605.15425)):

| Configuration | Retry cost, root-cause analysis | Retry cost, debugging |
|---|---:|---:|
| Monolithic prompt | 904 ± 17 tokens | 703 tokens |
| Static decomposition | 1,632 ± 145 tokens | 933 tokens |
| Runtime-structured | 436 ± 132 tokens | 460 tokens |

The middle row is the lesson: decomposition alone made retry cost *worse*,
because a failure in one subtask forced reruns of downstream subtasks. The
runtime-structured version reran only the failed subtask, cutting retry cost
by up to 51.7% versus monolithic and 73.2% versus static. The decomposition
must be an executable artifact — task files, a DAG, checkpoints — that the
runner can resume, not prose in a prompt that the model has to re-derive on
every retry. ReAcTree (AAMAS 2026) makes the same separation at the planning
layer: agent nodes reason, act, and expand the tree, while *control-flow
nodes* coordinate execution strategies; on the WAH-NL benchmark it roughly
doubled goal success versus ReAct (61% vs 31% with Qwen 2.5 72B)
([ReAcTree](https://arxiv.org/abs/2511.02424)).

## How production packages it

The invariants appear in every serious multi-agent setup, packaged
differently:

| System | What it owns | How the invariants appear |
|---|---|---|
| Supervisor pattern | bounded task tree | the default shape: one lead owns decomposition, workers get scoped leaves (invariant 4) |
| task-decomposer | plan → task files | mechanical handoff, 1–5 files per task, one task = one commit (invariants 1, 4) |
| k-sdd / cc-sdd | spec → long-running implementation | discovery → requirements → design → tasks, each task independently reviewed (invariants 1, 4) |
| mtix | micro issue manager | hierarchical decomposition with context chains, per-task microVM with default-deny network (invariant 2 at the execution boundary) |
| worktree isolation | per-task checkouts | a worktree per task, not per agent spawn, so coupled lanes fail loudly instead of silently (marcus #302) |
| dev-lead | contract-first orchestration | interface contract committed first, builders against the frozen contract (drift, invariant 4) |

Sources: [Anthropic's multi-agent lead-worker setup](https://www.anthropic.com/engineering/built-multi-agent-research-system),
[task-decomposer](https://github.com/shinpr/claude-code-workflows/blob/main/agents/task-decomposer.md),
[k-sdd](https://www.npmjs.com/package/k-sdd),
[mtix](https://github.com/hyper-swe/mtix),
[marcus #302](https://github.com/lwgray/marcus/issues/302),
[senacor](https://senacor.blog/introducing-a-dev-lead-agent-a-coordinator-forbidden-from-writing-code-and-why-it-has-to-be/).

The common thread is that none of them lets the decomposer execute its own
decomposition, and all of them make the DAG an artifact the runner can
resume — the two moves the failure cases above actually need.

## What the demo establishes, and what it does not

[decomposer.py](core/decomposer.py) makes three of the four invariants
mechanically checkable on the mission's real records, and its findings are
real: the site trio is one serial lane (width 2 total), and the public set
is width 1. It deliberately does not assign order inside a lane, and it
prints its own boundary — invariant 3 is declared "not mechanically checkable
without a constraint list for the intent", which is the reviewer's job.

What the demo does not establish is the frontier claim: *how good* a
decomposition is. That question needs a measure — the LLM-based
decomposition-quality eval that checks sub-goal coverage and granularity
([AgentEval](https://github.com/AgentEvalHQ/AgentEval)) — and a human review
of sufficiency. This chapter proves the shape is checkable and the topology
is decisive; it does not claim the split it produces is the correct one.
