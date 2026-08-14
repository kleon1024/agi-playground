---
status: draft
level: reference
label: From RAG to agentic RAG
---

# Retrieval stopped being a pre-step and became a tool

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** classic RAG retrieves once, stuffs context, and answers.
Agentic RAG makes retrieval a tool the agent calls mid-task, when it
decides it needs facts. What changed, and what stayed the same?

## The evolution

Classic RAG: embed the query, retrieve top-k, concatenate into the prompt,
answer. Agentic RAG: the agent decides *whether* to retrieve, *what* to
retrieve, and *when* — retrieval becomes a tool in the loop, subject to
the same permission and sandbox layers as any other tool. Industry
write-ups in 2026 describe hybrid retrieval shifting buyer-intent signals
(one documented case: 10.3% to 33.3% across a single quarter) as
retrieval moved from a fixed pre-step to a decision
([RAG landscape](https://atlan.com/know/agentic-ai/rag-vs-agentic-rag)).

## What stayed the same

The hard problems did not change: chunking, embedding quality, and
retrieval evaluation still decide quality. What changed is *agency* —
retrieval is now inside the loop, which means it can be wrong in new ways
(retrieving the wrong thing at the wrong step) and right in new ways
(fetching exactly the fact a tool result made necessary).

## What this means for this topic

The mission's harness has no retrieval — its tasks are self-contained.
The agentic version of RAG is what a platform adds when tasks need
external facts: a retrieval tool with schemas, sandbox, and permission
like any other. The stage's demo (a-sqlite-memory) is the storage floor;
this chapter is the retrieval evolution above it.

## What this does not say

It does not claim agentic RAG beats classic RAG universally — the right
shape depends on whether retrieval decisions belong inside the loop. It
maps the evolution and the unchanged core.
