---
status: draft
level: reference
label: Pi and the agent SDKs
---

# The harness you import instead of build

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** the stage built a harness by hand and reads production
harnesses as five decisions. The agent SDKs are the third family: a
harness delivered as a library, with the loop, tools, and permission
model as importable defaults. What do they standardize, and what do they
still leave to the platform around them?

## The three SDK shapes

**pi** ([earendil-works/pi](https://github.com/earendil-works/pi))
packages a unified multi-provider LLM API, an agent loop, a TUI, and a
coding-agent CLI into one toolkit — the composition layer for teams that
want the loop without building it.

**OpenAI Agents SDK** ships a built-in `Runner` loop with guardrails,
handoffs, and subagents, plus sandbox and dual-memory hooks
([docs](https://openai.github.io/openai-agents-python/)). The loop is a
library call; the policies around it are yours.

**Claude Agent SDK** exposes the same loop as
`query`/`receive_response` — the client drives the agent turn by turn,
which makes human-in-the-loop gates a natural fit
([docs](https://docs.claude.com/en/api/agent-sdk/overview)).

## What they standardize

The SDKs standardize the loop mechanics — tool schemas, message flow,
retry — the exact thing the mission's harness builds by hand. The
migration mapping (loop → Runner/query, tools → schemas, permission →
guardrails) is one-to-one with the five decisions.

## What they leave to the platform

Sandboxing, observability, evaluation, and policy remain external —
which is why the agentic-infrastructure and control-plane stages exist.
An SDK standardizes the cell; the platform governs the organism. The
distinction is the topic's spine: harness is the execution unit, not the
platform.

## What this does not say

It does not claim one SDK wins — each encodes a different default for
where the human sits (Runner inside, query outside). The reading is the
deliverable; the choice is the team's.
