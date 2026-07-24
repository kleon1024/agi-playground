---
status: draft
---

# 08 — Agents

## Scope

Agent harness engineering — the research identified this as the least-served
topic in the 2026 landscape. This track covers building an agent loop from
scratch: the core loop, tool schemas and calling, context window management,
sandboxed execution, and sub-agent/multi-agent patterns. The goal is to leave
with a harness you built and understand line-by-line, then be able to reason
about production harnesses (Claude Code, OpenHands, SWE-agent) as
elaborations on the same core loop.

## Prerequisites

`06-inference` (needs a served model — your own or an API model — to wrap in
a harness) and `07-evals` (harness-disclosed evaluation methodology applies
directly to whatever harness you build here).

## Planned lessons

1. `01-agent-loop-from-scratch` — the minimal read-act-observe loop, no
   framework.
2. `02-tool-schemas-and-calling` — defining and dispatching 2-3 tools, schema
   validation.
3. `03-context-window-management` — compaction, truncation, and memory
   strategies as the context grows.
4. `04-sandboxed-execution` — running tool actions (especially code
   execution) safely.
5. `05-sub-agents-and-multi-agent` — delegating to sub-agents, coordination
   patterns.
6. `06-harness-aware-evaluation` — evaluating the harness you built with the
   disclosure discipline from `07-evals`.

## Speedrun note

`01-agent-loop-from-scratch` through `04-sandboxed-execution` are the seed
lessons for speedrun stage `06-agent` (a minimal harness at mini-swe-agent
scale: loop, 2-3 tools, context window management, sandboxed execution,
wrapping the model served in stage `05-serve`).
