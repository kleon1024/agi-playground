---
status: draft
level: frontier
label: Tools and protocols
---

# How do an agent and a tool agree on a contract?

**Question:** stage 03 gave the harness three hand-written tool schemas.
Production agents compose tools across organizations — search, databases,
APIs, other agents — and the contract between agent and tool became a
protocol: MCP (JSON-RPC 2.0 with tools, resources, and prompts), plus SDKs
that run the loop for you. What does a tool protocol buy that a schema
cannot, and where does the platform hand off to the SDK?

**The artifact this stage follows** is a minimal tool protocol: a small
JSON-RPC-style server exposing three tools, wired to the stage 03 harness,
with the handshake, error, and capability-discovery paths recorded.

By the end you will be able to read any tool integration — a function call,
an MCP server, an SDK agent — as the same contract (discover, invoke, error,
result), and say which layer of the platform owns it.

**Before this:** [stage 03](../agent-loop/) owned its tools inline. This
stage externalizes the contract; [stage 12](../control-plane-and-governance/)
uses the same protocol thinking for the whole platform.

## What this stage decides

Where tool integration lives: inline in the harness, behind an MCP server,
or inside an SDK's managed loop. The decision changes what the platform can
compose — a protocol makes tools discoverable and swappable; inline schemas
make them fast and private.

## Planned chapters

- **a-minimal-tool-protocol** (local mechanism demo) — build the three-tool
  JSON-RPC server, wire it to the harness, and record a run that exercises
  discovery, invocation, and error return.
- **from-function-calling-to-mcp** — the evolution: schema-based function
  calling, then MCP's tools/resources/prompts primitives on JSON-RPC 2.0;
  what a standard protocol changes for tool ecosystems.
- **mcp-in-production** — transports, auth, and the reference split where
  the sandbox is the execution plane and MCP is the tool-discovery layer;
  Claude Managed Agents' headless sandbox + MCP tunnel pattern.
- **agent-sdk-composition** — OpenAI Agents SDK (built-in Runner loop,
  guardrails, handoffs, subagents), Claude Agent SDK
  (query/receive-response), and pi — the SDK as a harness you import instead
  of build.

## Evidence strategy

`a-minimal-tool-protocol` is the only run. The rest are dated surveys of
the MCP spec (2025-11-25 revision) and documented SDK behavior.

## Industrial grounding

MCP is JSON-RPC 2.0 with tools, resources, and prompts as its three
primitives. The OpenAI Agents SDK ships a built-in agent loop with
guardrails, handoffs, and subagents; pi (earendil-works) packages a unified
LLM API and agent loop into one toolkit. Reference architectures in 2026
split the sandbox (execution plane) from MCP (tool discovery), with managed
agents tunneling from headless sandboxes into MCP servers.
