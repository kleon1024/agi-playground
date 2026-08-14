---
status: draft
level: reference
label: When RAG belongs in an agent
---

# The decision is when to retrieve, not whether to retrieve

> Dated survey, 2026-08-14.

**Question:** retrieval inside an agent is not free — every retrieve call
is a tool call with latency, cost, and a chance of wrongness. When does
agentic retrieval earn its place, and when is it the wrong layer?

## When it earns its place

When the task is **open-world**: the agent cannot know in advance what
facts it needs. Repository-scale work is the canonical case — a refactor
needs API signatures, import graphs, and conventions that no prompt can
carry. Codebase retrieval (the stage's `codebase-retrieval` chapter) is
the same machinery pointed at code.

## When it is the wrong layer

When the facts are **stable and small** — an instruction file, a few
dozen conventions — retrieval is worse than simply putting them in
context. This is the two-layer memory split: instructions belong in the
static file (AGENTS.md), retrieved facts belong in the store. Retrieval
for facts that fit in context is latency with no benefit.

## The deciding question

"Will the agent's information need change during the task?" If yes, a
retrieval tool belongs in the loop. If no, context is the right layer.
The mission's tasks are the "no" case; repository-scale work is the "yes"
case. Getting this wrong in either direction is the classic failure —
vague prompts (too little context) or retrieval calls for facts already
known (too much machinery).

## What this does not say

It does not prescribe a retrieval stack. It gives the decision rule that
places retrieval on the correct layer of the memory map.
