---
status: draft
level: reference
label: Spec-driven development
---

# The spec is the first artifact, and the agent executes against it

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** spec-driven development — write the spec first, execute
against it, verify against it — became the industry's organizational
answer to agentic coding. What is the pipeline, and why did it win?

## The pipeline

GitHub Spec Kit (2026, open source, 72K+ stars, compatible with 30+
agents including Copilot, Claude Code, and Gemini CLI) enforces an
8-phase pipeline: constitution, context, spec, plan, execute, verify,
review, merge ([Spec Kit](https://github.com/github/spec-kit);
[DevOps.com](https://devops.com/githubs-spec-kit-puts-the-spec-back-in-software-development/)).
The spec is the contract the intent-to-plan stage teaches, scaled into a
team process.

## Why it won

It makes the ambiguous-cost problem measurable: a spec is reviewable
before execution, so the expensive mistakes happen before the expensive
work. It converts the human role from "review code the agent wrote" to
"approve the spec the agent will execute" — earlier, cheaper, and closer
to intent.

## What this means for this topic

The intent-to-plan stage's plan-as-contract is the spec in miniature; the
orchestration stage's spec-driven orchestration scales it across a
backlog. This chapter documents the team-level process both stages assume.

## What this does not say

It does not claim spec-driven development is easy — it is a discipline
that moves skill requirements to spec-writing and fast review. It maps
the pipeline and its organizational rationale.
