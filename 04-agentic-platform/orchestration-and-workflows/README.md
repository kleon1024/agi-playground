---
status: draft
level: frontier
label: Orchestration and workflows
---

# One agent fixed one bug. How do you organize a task that needs twenty?

**Question:** every stage so far has been a single harness on a single
task. Real engineering work — a monorepo migration, a dataset cutover, a
deployment rewrite — is many tasks with dependencies, and the industry has
two answers for organizing it: deterministic workflows (the agent fills
cells in a skeleton the team controls) and multi-agent coordination (agents
delegate to each other). The 2025–2026 production record is blunt about
which one fails less. What is the evidence, and when does each apply?

**The artifact this stage follows** is a workflow: the six real tasks from
stage 00 organized as a dependency graph, executed by an orchestrator that
dispatches to workers and collects results — with the recorded run showing
what determinism costs and buys.

By the end you will be able to take any complex task, choose between a
workflow and free multi-agent coordination, and defend the choice with the
production failure record — not vibes.

**Before this:** [stage 10](../tools-and-protocols/) made tools composable.
This stage makes tasks composable; [stage 12](../control-plane-and-governance/)
governs the result.

## What this stage decides

Where the planning happens: in a deterministic skeleton the team wrote, or
in the LLM's head. Anthropic's 2026 guidance is explicit — for structured,
mission-critical work, orchestrate the steps deliberately and let the agent
fill the gaps; free agents are for exploratory tasks. This stage makes that
distinction operational.

## Planned chapters

- **the-workflow-taxonomy** — Anthropic's patterns (prompt chains, routing,
  parallelization, orchestrator-workers, evaluator-optimizer) and the 2026
  coordination extensions (agent teams, message bus, shared state).
- **when-to-orchestrate** — the decision rule: deterministic skeleton with
  LLM cells for mission-critical work, free agent for exploration; what
  changes at each point of the spectrum.
- **why-multi-agent-fails** — the production record: AutoGen's
  non-terminating conversations as its most frequent failure mode, command
  races and state hallucination across CrewAI/AutoGen/LangGraph, and the
  fixes (aggressive termination, durable state) the industry converged on.
- **spec-driven-orchestration** — orchestrating from an issue tracker:
  OpenAI's Symphony (an open spec for many Codex agents driven by Linear),
  spec-in/PR-out as an organizational redesign, and the "ticket quality is a
  productivity input" finding.
- **a-minimal-orchestrator** (local mechanism demo) — an orchestrator that
  dispatches the six real tasks to workers under a deterministic skeleton,
  records per-task results, and reports what the skeleton cost versus a
  free-loop baseline.

## Evidence strategy

`a-minimal-orchestrator` runs against the mission's real task set and is
recorded. The rest are dated surveys of Anthropic's published patterns and
the multi-agent production postmortems, cited inline.

## Industrial grounding

Anthropic's workflow taxonomy and 2026 coordination patterns are the
reference taxonomy; their guidance is to orchestrate structured work
deliberately. Production write-ups of AutoGen/CrewAI/LangGraph deployments
in 2025–2026 report non-terminating conversations, command races, and state
hallucination as the dominant failures, fixed with aggressive termination
and persistence. OpenAI's Symphony (2026) and GitHub Spec Kit both push
spec-first orchestration from an issue tracker as the organizing pattern.
