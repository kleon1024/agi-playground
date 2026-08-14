---
status: draft
level: frontier
label: Intent to plan
---

# Intent is not text. It is a constraint set. What does it take to extract it?

**Question:** the mission's task set assumes intent arrives as a failing
test. Real work arrives as a sentence: *"the search box is slow"*, *"can
we add caching"*, *"fix the thing that broke last night"*. The difference
between that sentence and a task record is not verbosity — it is that the
record contains a *constraint set* (exact file, exact test, exact
verification command) and the sentence does not. This stage is about the
conversion: what intent actually is, where it gets lost, and what
mechanisms force it into a checkable form.

**The artifact this stage follows** is the gap itself, made concrete. Here
is the original human artifact that produced one of this mission's tasks —
the commit message of the bug it fixed:

```text
fix(serve): attend past the first token in every cached decode step
```

And here is the task record the miner extracted from the same repository:

```json
{"task_id": "private-b81c414",
 "subject": "fix(serve): attend past the first token in every cached decode step",
 "source_files": ["missions/01-language-model-agent/05-serve/core/engine.py"],
 "target_tests": ["tests/test_decode_correctness.py"],
 "test_command": ["uv", "run", "--group", "torch", "pytest", "-q",
                  "tests/test_decode_correctness.py"]}
```

The commit message holds the intent; the record holds the constraints.
Everything between them — what was extracted, what was inferred, what was
left out — is this stage's subject. By the end you will be able to take
any request, name the constraints hidden in it, list the ones that are
missing, and read any production planning flow as a machine for closing
that gap.

**Before this:** [stage 00](../task-set/) defined what makes a task
scorable. This stage is the conversion that produces one.

## Intent is a constraint set, not a sentence

The claim that unlocks this stage: when a human says *"fix the search
box"*, what they actually hold is a set of constraints — the box must be
fast, it must still return the same results, it must not break the filters
— plus some constraints they did not think to state. The sentence is a
compression of that set, and compression loses information by design.

The task record is the same constraint set in a lossless-enough form:

| Constraint the intent contains | Where it lives in the record |
|---|---|
| what file is wrong | `source_files` |
| what correct looks like | `target_tests` |
| how correct is decided | `test_command` |
| what must not break | (implicit — the regression check in [stage 03](../agent-loop/)) |
| why this matters | dropped — not in the record |

The last two rows are the point. *What must not break* is a constraint in
every real intent, and the record does not carry it — the harness had to
re-derive it as a regression check. *Why this matters* (the intent's
reason) is dropped entirely, and the record is correct to drop it: the
reason does not change what the tests check. Intent formalization is
exactly this — deciding which constraints the executable form must carry
and which it can discard.

## Intent has three levels, and agents get them confused

Human intent is not one thing. It arrives at three levels, and the failure
mode of every vague-request story is a level mismatch:

1. **Strategic intent** — why the work exists. "We are losing users on
   slow search." This is not executable and never should be.
2. **Task intent** — what the work is. "Make search return results under
   200ms for the top 100 queries." This is what a task record formalizes.
3. **Execution intent** — how the work is done. "Add a Redis cache keyed
   by query." This is a *solution*, and it is where requests most often
   get stuck.

The classic failure: a request that states execution intent ("add
caching") without task intent ("search is slow, here is the query set,
here is the budget"). An agent that executes the solution without the
task cannot verify it did the right thing — a cache can be added and the
search can stay slow. The task record exists precisely to force intent
down to the task level, where it is verifiable, and to keep execution
intent as the agent's decision rather than the requester's assumption.

## The loss chain: where intent evaporates

Between a human thought and a passing test, intent crosses five surfaces,
and each one leaks:

```text
thought → conversation → ticket → spec/plan → code → passing test
```

| Surface | What is lost there | What catches it |
|---|---|---|
| thought → conversation | tacit knowledge, context the speaker assumes | grounding (discover the repo, don't ask) |
| conversation → ticket | the conversation's clarifications | ticket hygiene — or the loss is accepted |
| ticket → spec/plan | constraints never stated | plan review by a human who knows the domain |
| spec/plan → code | the plan's exactness | tests — the only lossless surface |
| code → passing test | the test's blind spots | regression and generality checks ([stage 14](../verification-and-evals/)) |

Only the last surface is lossless: a passing test is a machine-checkable
fact. Everything upstream of it leaks, which is why the industry's answer
is not "write better" — it is to make each surface's loss *detectable*.
The plan makes the ticket's loss visible before execution; the test makes
the code's loss visible after.

## The three moves, as loss control

This reframing makes the three production moves mechanical instead of
advisory:

**Grounding controls the thought → conversation → ticket losses.** Codex's
plan mode rule — *"eliminate unknowns in the prompt by discovering facts,
not by asking the user"* ([openai/codex](https://github.com/openai/codex/pull/10195))
— is a loss-control rule: the tacit context the requester assumed is
recovered from the repository instead of being re-negotiated. Jules does
the same mechanically: clone, inspect, then plan.

**Exactness controls the ticket → plan loss.** A plan-only output — exact
file paths, exact structures, exact signatures, nothing else — is a
constraint set with the ambiguity removed. The mission's
[a-minimal-planner](a-minimal-planner/) demo produces exactly this shape
from a task record, with no model in the loop:

```text
# Plan: attend past the first token in every cached decode step

**Task:** `private-b81c414`

## Files to change
- `missions/01-language-model-agent/05-serve/core/engine.py`

## Tests this must satisfy
- `tests/test_decode_correctness.py`

## Verification
uv run --group torch pytest -q tests/test_decode_correctness.py

## What the plan does not claim
- It does not claim the fix; the test decides that.
- It does not claim the ground truth: that stays in the task record.
```

**The approval gate controls the tacit-constraint loss.** The one loss no
mechanism can close is the constraint the requester never stated and the
agent never discovered — "don't break the filters". A human reviewing the
plan before execution is the only reader who can supply it. The gate is
not ceremony; it is the loss-control point for the most expensive
category of leak ([Tembo, 2026](https://www.tembo.io/blog/autonomous-coding-agents)).

## What "spec-driven" is and is not

Spec-driven development is not a fourth move. It is the team-level
packaging of the same three: the spec is the grounded, exact plan, and the
spec-review phase is the gate. GitHub Spec Kit's 8-phase pipeline
([Spec Kit](https://github.com/github/spec-kit)) exists to make the three
moves routine across 30+ agents; the moves themselves are what any single
harness needs. Confusing the packaging (spec files, phase names) with the
mechanism (loss control) is how this stage reads as "just write a spec".

| Flow | Grounding (loses 1–2) | Exactness (loses 3) | Gate (loses tacit) |
|---|---|---|---|
| Codex plan mode | discover facts first | plan-only output | explicit approval |
| Jules | clone + inspect | draft plan | approval before diff |
| Spec Kit | constitution + context phases | spec as first artifact | spec review |
| Mission planner demo | task record (mined) | files/tests/verification | no gate — demo |

## What this stage does and does not establish

It establishes the mechanism: intent as a constraint set, the loss chain,
and the three moves as loss control, with the mission's own task record as
the worked example. The industrial flows confirm the shape at team scale.

What it does not establish — yet — is the measurement that would price the
moves: does plan-gating change resolve rate or cost per resolved task on
the mission's own set? That is a planned run, not a claimed result, and
the stage says so instead of pretending.

## Sub-chapters

- **[when-the-request-is-vague](when-the-request-is-vague/)** — the
  ambiguity taxonomy: each kind of missing constraint, its signal, and the
  move that closes it.
- **[the-plan-as-contract](the-plan-as-contract/)** — the plan as the
  intent's verifiable projection: what it must keep, what it may drop, and
  why plan-only is a property, not a style.
- **[spec-driven-development](spec-driven-development/)** — the 8-phase
  pipeline as the three moves institutionalized.
- **[a-minimal-planner](a-minimal-planner/)** (verified demo) — the
  constraint extractor that produced the artifact above, run on the
  mission's real tasks.
- **[decomposing-a-large-intent](decomposing-a-large-intent/)** (verified
  demo) — how an intent that spans several leaves becomes a tree of
  verifiable work: the four decomposition invariants, the failure directions
  that break them, and the topology-derived decomposer run on the mission's
  real task sets.
