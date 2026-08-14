---
status: draft
level: reference
label: The workflow taxonomy
---

# Chains, routing, parallelization, orchestrator-workers, evaluator-optimizer

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** before multi-agent coordination there were workflows. The
industry's reference taxonomy — Anthropic's building-effective-agents
patterns — names five deterministic shapes plus the free agent. What is
each shape, and when does it apply?

## The five shapes

**Prompt chains** — fixed sequence: each step's output feeds the next.
For predictable pipelines where the order never changes.

**Routing** — classify the input, dispatch to the right handler. For
tasks that split into known buckets.

**Parallelization** — fan out independent work, combine results. For
tasks decomposable into independent chunks.

**Orchestrator-workers** — an orchestrator dynamically decides which
workers run and synthesizes their output. Unlike a free agent loop, the
orchestrator does not loop indefinitely
([Anthropic](https://www.anthropic.com/research/building-effective-agents)).

**Evaluator-optimizer** — one generator, one evaluator, iterate until the
evaluator passes. The verification loop made into a workflow shape.

## What the taxonomy teaches

The five shapes are the deterministic skeleton the stage argues structured
work needs. The mission's a-minimal-orchestrator demo implements the
orchestrator-workers shape with deterministic workers; the judge demo is
the evaluator-optimizer shape in miniature.

## What this does not say

It does not claim workflows replace agents — the taxonomy's own framing is
that workflows are for predictable work and agents for open-ended work.
It provides the vocabulary the stage's when-to-orchestrate decision uses.
