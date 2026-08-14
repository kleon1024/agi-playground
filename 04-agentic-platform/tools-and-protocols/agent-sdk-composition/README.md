---
status: draft
level: reference
label: Agent SDK composition
---

# The loop as a library: what an SDK owns and what it leaves you

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** the harness-comparison stage reads production harnesses as
five decisions. The agent SDKs package the loop as a library — and by
doing so, move the real work to the policies around the loop. What does
each SDK standardize, and what stays yours?

## The three SDKs

**OpenAI Agents SDK** — a built-in `Runner` loop with guardrails, handoffs,
subagents, sandbox hooks, and dual memory
([docs](https://openai.github.io/openai-agents-python/)). The loop is a
library call; policies are configuration.

**Claude Agent SDK** — `query`/`receive_response` drives the agent turn by
turn, keeping the human gate inside the loop
([docs](https://docs.claude.com/en/api/agent-sdk/overview)).

**pi** — unified multi-provider API plus loop plus TUI plus coding-agent
CLI in one toolkit ([earendil-works/pi](https://github.com/earendil-works/pi)).

## What the SDK owns

Tool schemas, message flow, retry, and loop mechanics — the exact thing
the mission's harness builds by hand. The migration mapping to the five
decisions is one-to-one: loop → Runner/query, tools → schemas, permission
→ guardrails, context → memory hooks, sandbox → SDK sandbox config.

## What stays yours

Sandboxing at the boundary, observability, evaluation, and policy. An SDK
is the cell; the platform is the organism. This is the topic's spine made
concrete: harness is the execution unit, not the platform.

## What this does not say

It does not claim one SDK wins — each encodes a different default for
where the human sits. The composition decision is per-team; the reading
is the deliverable.
