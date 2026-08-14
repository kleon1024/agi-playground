---
status: draft
level: frontier
base: none
label: Orchestration and workflows
---

# One agent fixed one bug. How do you organize a task that needs twenty?

**Question:** every stage so far was one harness on one task.
[Decomposing a large intent](../intent-to-plan/decomposing-a-large-intent/)
produced the map — the width-2 DAG where a serve fix runs beside a serial
site-docs lane. But a map is not execution. Real engineering work — a
monorepo migration, a dataset cutover — is dozens of tasks with
dependencies, and there are two ways to run them: a deterministic skeleton
the team wrote, with the agent filling the gaps, or free multi-agent
coordination, where agents delegate to each other. The 2025–2026
production record is blunt about which fails less. What is the evidence,
and when does each apply?

**The artifact this stage follows** is [a-minimal-orchestrator](a-minimal-orchestrator/),
the mission's real tasks dispatched through a deterministic skeleton
([record](a-minimal-orchestrator/runs/2026-08-14-orchestrator.md)). No
model was called — the point is to see the skeleton before any cell is
filled. Every production workflow below is that skeleton, at scale.

**Before this:** [stage 10](../tools-and-protocols/) made tools composable.
This stage makes tasks composable.

## Two ways to run twenty tasks

The two answers differ in where the plan lives
([the-workflow-taxonomy](the-workflow-taxonomy/),
[when-to-orchestrate](when-to-orchestrate/)):

| | Deterministic workflow | Free multi-agent coordination |
|---|---|---|
| Where the plan lives | in a skeleton the team wrote — steps, owners, inputs, outputs | in the LLM's head, negotiated between agents |
| Termination | structural — the plan is fixed, the record is complete by construction | negotiated — agents stop when they agree |
| Failure mode | a step that does not fit the skeleton | conversation that never ends, work done twice |
| Right for | mission-critical, structured work | exploratory tasks with no known shape |

Anthropic's 2026 guidance is explicit: orchestrate the steps deliberately
for structured work and let the agent fill the gaps; free agents are for
exploration. The interesting thing is that the production failure record
backed this up faster than anyone expected — not because coordination is
impossible, but because of *how* free coordination breaks.

## Why free multi-agent coordination fails

Production write-ups of the 2025–2026 framework wave — CrewAI,
AutoGen/AG2, LangGraph — converge on three failure modes
([why-multi-agent-fails](why-multi-agent-fails/)):

1. **Non-terminating conversation.** The highest-frequency AutoGen
   failure. Two agents negotiate, neither can satisfy the other, and the
   loop does not end. The fix deployed in practice is an aggressive
   termination condition — which one write-up calls, in its own words, "a
   parent stepping in."
2. **Command races and state hallucination.** With no shared state
   primitive, agents act on stale or invented beliefs about what another
   agent already did. The arithmetic one write-up states plainly: two
   agents working together does not double throughput, it doubles faults.
3. **No audit surface.** A conversation is not a record. When work is
   negotiated, nobody can later say which agent decided what, or why.

All three are the same disease: the coordination is left to conversation,
and conversation is not durable, not bounded, and not reviewable.

## The skeleton, read

[a-minimal-orchestrator](a-minimal-orchestrator/) shows the contrast
mechanically. Two workers, each owning one bounded check, dispatched and
collected by a fixed plan:

```text
[PASS] private-b81c414: task-record=True; verification-contract=True
[PASS] private-354c352: task-record=True; verification-contract=True

2/2 tasks passed all deterministic gates; no model called.
```

The orchestrator does not negotiate with the workers. It dispatches,
collects, and records. Termination is structural — the dispatch plan is
fixed and the record is complete by construction — which is the exact
opposite of the free-agent failure mode where a parent has to step in and
end the conversation. The skeleton is not a stylistic preference; it is
the substrate that makes termination, auditing, and resumption possible.
The "no model called" line is deliberate: the skeleton is shown before any
cell is filled, because the argument is about the shape, not the
intelligence inside it.

## The skeleton, written down before execution

The industrial version makes the skeleton an artifact the team reviews
before any agent runs ([spec-driven-orchestration](spec-driven-orchestration/)):
OpenAI's Symphony drives many Codex agents from Linear issues, GitHub Spec
Kit turns a spec into task files, and both report the same finding — the
quality of the ticket is a productivity input, because a skeleton built
from a vague spec fails the same way a free conversation does. This is the
[intent stage's plan-as-contract](../intent-to-plan/) at fleet scale: the
skeleton is the plan, and the plan is a contract each worker executes
against.

## When the skeleton is the wrong shape

The boundary cuts both ways. If the task has no known shape — "explore
this codebase and tell me what is worth knowing" — a fixed skeleton forces
cells onto a problem that does not have them, and a free agent is the
honest tool. The decision rule is not "always orchestrate": it is
*structured work gets a skeleton, exploration gets a leash*. The mission's
own work sits firmly on the skeleton side — every task arrives as a test
to satisfy, which is a shape someone already defined.

## What this stage does and does not establish

It establishes the mechanism: the deterministic skeleton as the substrate
for termination, auditing, and resumption, verified by the recorded
dispatch on real tasks. The production claims — Anthropic's guidance,
AutoGen's non-terminating conversations, the fault-doubling arithmetic —
are dated surveys with sources cited.

It does not claim the skeleton improves quality; the model cells are
absent by design, and that measurement belongs to the production record,
not to this demo. And it does not claim free coordination never works — it
claims the production record says where it works, and that the mission's
structured task set is not that place.

**Next:** the work is orchestrated. Who sees the result, and who decides
it is allowed to land — [control plane and governance](../control-plane-and-governance/).
