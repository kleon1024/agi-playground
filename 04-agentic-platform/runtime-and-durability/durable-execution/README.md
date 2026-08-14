---
status: draft
level: reference
label: Durable execution
---

# Journal replay, idempotency, and the engines that do it

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** the checkpointer demo persisted completed work. Production
durable execution persists *every* step — every LLM call, tool result,
and routing decision — so an agent survives a crash and resumes exactly
where it stopped. What are the engines, and what does each one guarantee?

## The engines

**Temporal** — from Uber's ride-matching system. Makes individual
workflows durable via journal replay; needs worker versioning (build IDs)
to migrate safely ([Temporal](https://temporal.io/blog/building-durable-agents-with-temporal-and-ai-sdk-by-vercel)).

**Restate** — from distributed-systems engineers at AWS. Pins executions
to immutable deployment URLs and makes *systems* durable — sessions,
approvals, and state, not just one workflow loop
([Restate](https://docs.restate.dev/ai/patterns/durable-agents)).

**Durable Objects (Cloudflare)** — every agent runs on a stateful
micro-server with its own SQL database, WebSocket connections, and
scheduling ([Cloudflare Agents](https://developers.cloudflare.com/agents/)).
Anthropic's Claude Managed Agents run on sandboxes whose sessions keep
state across inactivity ([Anthropic + Cloudflare](https://itbrief.co.uk/story/cloudflare-anthropic-launch-claude-agents-on-sandboxes)).

## The mechanism they share

Journal replay: every step is appended to a durable log, and recovery
replays the log to reconstruct state. The two design questions are
idempotency (a replayed tool call must not run twice) and versioning
(a resumed workflow must not run on old code). Thoughtworks' 2026 radar
lists "ignoring durability in agent workflows" as a technique to avoid
([radar](https://www.thoughtworks.com/radar/techniques/ignoring-durability-in-agent-workflows)).

## Why this sits in the platform

Durability is the substrate the orchestration stage's skeleton runs on: a
deterministic workflow that can crash and resume is a workflow that can
run unattended for hours. The checkpointer demo is the 200-line version
of the guarantee; the engines are the production version.

## What this does not say

It does not claim one engine wins — Temporal and Restate differ in what
they make durable (workflow vs system). It maps the guarantee and the
mechanism; the choice is per-deployment.
