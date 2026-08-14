---
status: verified
level: frontier
base: scratch
label: Decomposing a large intent
verified: 2026-08-14
---

# A large task arrives as a sentence. How do you turn it into work agents can run?

**Question:** [stage 02](../) turned one sentence into one task record — a
leaf with one test that decides done. Real reports hold several tasks at
once: *"the site docs pipeline is broken, and the serving engine is wrong"*.
If you fan one agent out per clause, they collide on the same files. If you
serialize everything, you leave parallelism unused. Before any agent runs,
how do you decide which parts can run in parallel and which must wait?

**The artifact this chapter follows** is one composite intent built from this
mission's real history — *"make the repository's correctness signals green
again"* — and what [a rule-based decomposer](core/decomposer.py) does with it
([run record](runs/2026-08-14-decomposer.md)). No model is called. The point
is that a correct decomposition is decided by the code, not by the model and
not by the sentence.

**Before this:** [stage 02's constraint-set model](../). This chapter takes
the step from one leaf to many.

## Why "one agent per clause" collides

The composite intent is not invented. It is the sentence behind four commits
that really exist in this repository's history — one fixing the serving
engine, three fixing the site's docs pipeline:

```text
INTENT: Make the repository's correctness signals green again

clause 1 -> private-b81c414   fix the serving engine's cached decode step
clause 2 -> private-354c352   stop escaping angle brackets in docs
clause 3 -> private-642074a   restore the pages the sidebar dropped
clause 4 -> private-be65ef6   drop generated numbers from titles
```

The naive move is to give each clause its own agent and run all four at
once. That is where it breaks. Clauses 2, 3, and 4 all change the same file,
`site/sync-docs.py` — three agents writing one file in an order nobody
chose. Whoever runs second overwrites the first.

This is not a hypothetical. The marcus project measured the same failure:
it split "movement" and "food collection" into separate tasks, both lived in
the same function, and one of the two agents wrote 100% of the product code
while the other produced nothing ([marcus #267](https://github.com/lwgray/marcus/issues/267)).
The sentence is a noun-level view of the work; the file is the ground truth
agents actually write. Split by the sentence, and the collision is invisible
until it happens.

## What a large intent actually adds

Stage 02's model still holds: a leaf is a constraint set with one done
condition. A large intent is the same model at one level up — the constraint
set now spans several leaves, and satisfying it requires deciding *how the
leaves relate*.

Two structures appear, and a flat list hides both:

```text
The tree (who owns what)              The DAG (what waits for what)

intent                                  b81c414 (serve)       ─┐
 ├── serve correctness                 └──────────┬──────────┤ width 2
 │    └── b81c414                                   │         │
 └── site docs pipeline               354c352 → 642074a → be65ef6
      ├── 354c352                      (three tasks, one file:
      ├── 642074a                       serial lane, order not yet known)
      └── be65ef6
```

The tree is ownership — which subgoal each task belongs to. The DAG is
ordering — what must wait for what. The decomposition's job is to find both,
and the second one is the hard one.

## Shared files are the ground truth

The sentence says "fix escaping, fix the sidebar, fix ordering" — three
nouns. The code says "all three touch `site/sync-docs.py`" — one file. The
file wins, because it is what agents actually write.

The mechanism is a file-overlap check. Two tasks that share a source file
cannot be independent parallel agents — whoever runs second contends with the
first writer. So: draw an edge between every pair of tasks that share a
file, and the connected components are *lanes*. A lane whose members all
share files must run serially. This is marcus's topology check
([#267](https://github.com/lwgray/marcus/issues/267)) made mechanical: his
team proposed the file-overlap matrix to decide between feature-based and
layer-based splits; the demo runs that matrix on every pair.

## Run it, and read what the code says

The decomposer ([core/decomposer.py](core/decomposer.py)) needs no model and
no API key. It reads this mission's task records and prints the lanes:

```bash
cd 04-agentic-platform/intent-to-plan/decomposing-a-large-intent/core
python3 decomposer.py --tasks ../../../tasks/candidates.jsonl \
    --intent "Make the repository's correctness signals green again"
```

The output is the artifact this chapter promised:

```text
Lane 1 · touches missions/01-language-model-agent/05-serve/core/engine.py (1 leaf) · independent
└── private-b81c414  fix(serve): attend past the first token in every cached decode step  [done: tests/test_decode_correctness.py]

Lane 2 · shares site/sync-docs.py (3 leaves) · coupled -> serial
├── private-354c352  fix(site): stop escaping angle brackets inside inline code  [done: tests/test_sync_docs.py]
├── private-642074a  fix(site): restore the pages the explicit sidebar dropped  [done: tests/test_sync_docs.py]
└── private-be65ef6  fix(site): drop generated numbers from titles and order indexes correctly  [done: tests/test_sync_docs.py]

DAG width (parallel lanes): 2
```

Two results, both worth stopping on.

First, the width is 2, not 4 and not 1. Only the serve task can run
independently; the three site tasks form one serial lane. So at most two
agents can work without contending — and that number comes from the files,
not from the sentence.

Second, the lane gives no order. The decomposer prints `354c352 → 642074a →
be65ef6` as a lane but refuses to order it, because the records contain no
design doc saying which fix comes first. Deciding that order is a design
decision, which is exactly why production decomposers are built as separate
roles: the task-decomposer in the claude-code-workflows collection is defined
as a mechanical handoff that preserves dependencies and verification but is
forbidden from introducing new design decisions
([task-decomposer](https://github.com/shinpr/claude-code-workflows/blob/main/agents/task-decomposer.md)),
and the senacor dev-lead agent is *forbidden from writing code* so it cannot
grade its own plan ([senacor, 2026](https://senacor.blog/introducing-a-dev-lead-agent-a-coordinator-forbidden-from-writing-code-and-why-it-has-to-be/)).

Run the same decomposer on the mission's public candidate set and you get the
other extreme: six tasks, every one touching `more_itertools/more.py`, all
pairwise overlap 1.00 — width 1. "Harden the itertools library" sounds like
six parallel jobs and is one serial lane. The width of a decomposition is a
property of the code, not of the intent's size.

## What the tree does not decide

The demo's honest boundary is printed in its own output: it checks that every
leaf has a done condition, it finds the lanes, and then it stops. Three
things remain outside it, and each one is where the frontier actually is.

**Order inside a lane.** Who runs first in the site trio needs the design
doc, not the overlap matrix. The decomposer says so instead of guessing.

**Coverage.** Does the tree cover everything the intent meant? The demo
cannot check this without a constraint list for the sentence — it declares
the question the reviewer's job, and LLM-based decomposition-quality evals
exist to measure exactly this
([AgentEval](https://github.com/AgentEvalHQ/AgentEval)).

**Where the decomposition lives.** The deepest question is not how to split
but whether the split is an artifact the runner can resume. A 2026 study ran
three configurations of the same agentic workloads: a monolithic prompt, a
static decomposition with fixed subtasks, and a runtime-structured version
where the flow is executable control logic. Static decomposition made retry
cost *worse* — 1,632 ± 145 tokens versus 904 ± 17 monolithic on root-cause
analysis — because a failure in one subtask forced reruns of the downstream
ones. The runtime-structured version reran only the failed subtask: 436 ± 132
tokens, up to 51.7% lower than monolithic and 73.2% lower than static
([arXiv:2605.15425](https://arxiv.org/abs/2605.15425)). The decomposition
has to be a DAG the runner can checkpoint, not prose the model re-derives on
every retry.

## Where this leads

The tree answered one question: *what can run in parallel*. The next question
is what happens when you actually let it — parallel workers editing the same
repository need worktrees, contracts, and a coordinator, which is the
[orchestration stage](../../orchestration-and-workflows/)'s subject. The
decomposition is what makes that coordination possible in the first place:
it is the map that says where the parallel lanes are and where they are not.
