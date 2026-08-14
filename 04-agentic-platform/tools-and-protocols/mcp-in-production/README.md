---
status: draft
level: reference
label: MCP in production
---

# The reference split: sandbox executes, MCP discovers

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** a protocol is one thing; a production integration is
another. Where does MCP sit in the platform, and what does a production
deployment actually look like?

## The reference split

2026 reference architectures separate the two planes: the **sandbox is the
execution plane** (where tool calls run, isolated), and **MCP is the
tool-discovery layer** (what tools exist and how to call them)
([blaxel.ai architecture write-up, 2026-04](https://blaxel.ai/blog/mcp-and-code-execution-sandbox)).
An agent in a headless sandbox reaches MCP servers through tunnels — the
Claude Managed Agents pattern of headless sandbox plus MCP tunnel
([Anthropic](https://platform.claude.com/docs/en/agents/sandboxing)).

## Production concerns

**Transports** — stdio for local, HTTP/SSE for remote, with streaming for
long tool calls.

**Auth** — the credential proxy pattern (agent receives capabilities, not
tokens) applies to MCP servers exactly as it does to any tool: the
control-plane chapter's no-secrets-no-authority invariant.

**Scoping** — a repository exposes an allowlist of servers; adding one is
a policy change, not a runtime request.

## Why this sits in the platform

MCP is how the platform's tool surface stays composable: the sandbox
executes, the protocol discovers, the control plane authorizes. The
mission's tool protocol demo is the contract in miniature; this chapter
maps the production wiring.

## What this does not say

It does not claim MCP is mature everywhere — auth and streaming
specifications are still settling. It maps the reference shape the
industry is converging on.
