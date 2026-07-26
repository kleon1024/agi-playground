---
status: draft
---

# Speedrun 06 — Agent

## Goal

Wrap the served model in a minimal agent harness you built: a loop, a small
tool set, context management, and sandboxed execution.

## Deliverable

A minimal harness at mini-swe-agent scale: an agent loop, 2-3 tools, context
window management, and sandboxed execution of tool actions, wrapping the
model served in `05-serve`.

## Anchor project

mini-swe-agent (see `capabilities/act-coordinate/LANDSCAPE.md` for the toy/production
mapping). Seed lessons: `capabilities/act-coordinate/README.md`,
`01-agent-loop-from-scratch` through `04-sandboxed-execution`.

## Verification criterion

No verified run yet — depends on `05-serve` landing first. When built, its
`runs/` entry must show: the exact harness invocation, the tool set and
their schemas, a transcript of at least one full task run (with the harness
disclosed per `platform/evaluation-observability`' harness-disclosed evaluation discipline),
and wall-clock time per task.
