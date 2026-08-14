---
status: draft
level: reference
label: Memory tiers
---

# Working, episodic, semantic: the three-tier production stack

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** agent memory in production is tiered, not monolithic. What
are the tiers, what stores occupy them, and what does the industry
actually agree on?

## The tiers

**Working memory** — what is in the current context window: the session's
conversation and tool state. Redis or an in-process buffer in the
production stack.

**Episodic memory** — past sessions, retrievable on demand: the Codex
rolling summaries, Claude auto-memory, Mem0's fact store. Vector
retrieval for open-ended recall.

**Semantic/long-term memory** — facts and relationships that outlive
sessions: Mem0's timestamped facts with TTLs, Zep's temporal knowledge
graphs, Letta's tiered OS-style memory ([2026 comparison](https://atlan.com/know/best-ai-agent-memory-frameworks-2026/)).

## What the industry agrees on

Start with vector, add graph when entity relationships matter; keep
working memory in-process; and treat forgetting as a first-class feature —
Mem0 ships TTLs, Zep models valid-at/recorded-at on every edge
([memory evaluation](https://futureagi.com/blog/evaluating-agent-memory-systems-2026)).
The measured claim: selective fact-based memory cut token cost by over
90% and p95 latency by 91% versus full-history prompting (Mem0's paper,
2025).

## What this means for this topic

The mission's a-sqlite-memory demo occupies the semantic tier with
keyword recall — deliberately the weakest retrieval, to show the floor.
The surveys above document the vector/graph ceiling and the forgetting
primitives the floor lacks.

## What this does not say

It does not claim one stack is universal — tier adoption follows the pain
(spanning sessions first, entity reasoning second). It maps the tiers and
their stores.
