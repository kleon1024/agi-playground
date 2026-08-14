---
status: draft
level: reference
label: From function calling to MCP
---

# One schema per model, or one protocol for everything

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** before MCP, tool integration was a schema in a prompt — one
per model, per harness, per deployment. MCP made the contract a protocol:
JSON-RPC 2.0 with tools, resources, and prompts. What exactly did the
protocol add?

## The evolution

Function calling: the harness declares tool schemas to the model, the
model returns a structured call. MCP: the same shape standardized across
servers and clients — a tool registry the client discovers, JSON-RPC 2.0
transport, and three primitives (tools for actions, resources for data,
prompts for reusable instructions)
([MCP spec](https://modelcontextprotocol.io/specification/2025-11-25)).

## What the protocol buys

**Discoverability** — a client asks what tools exist instead of hard-coding
them (the a-minimal-tool-protocol demo's first operation).

**Swappability** — a tool is a server; replacing it is a config change.

**Ecosystem** — one client speaks to many servers, so a repository's tools,
databases, and services become the same protocol surface.

## What it does not solve

It does not solve sandboxing, permissions, or auth — those live in the
layers the execution-environment and control-plane stages map. MCP
standardizes the contract between agent and tool; it does not govern what
the agent may do with a tool.

## What this does not say

It does not claim MCP replaces function calling everywhere — in-process
schemas remain faster and simpler for private tools. It maps the
standardization step and its boundary.
