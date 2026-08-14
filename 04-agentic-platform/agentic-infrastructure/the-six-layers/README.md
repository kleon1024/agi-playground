---
status: draft
level: reference
label: The six layers
---

# What actually sits under a production agent

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** the control plane governs the fleet, but the fleet runs on
infrastructure: inference, sandboxes, stores, registries, observability,
evaluation. What are the six layers, and which cloud products occupy
them?

## The six layers

**Inference** — the model serving layer: vLLM, SGLang, hosted endpoints.
Every tool call needs tokens; inference is the hard dependency.

**Sandbox execution** — where agents run: E2B's Firecracker microVMs,
Modal, Daytona, NVIDIA's OpenShell — the fastest-growing layer in the
enterprise AI stack ([Northflank's 2026 stack](https://northflank.com/blog/ai-stack-for-enterprise-engineering)).

**Data and memory stores** — vector databases, SQLite-first memory, and
the repositioning of Databricks and Snowflake as AI memory systems
([Deltastring analysis](https://news.deltastring.com/story/the-internet-is-being-rebuilt-for-machines-4312)).

**Tool registries and MCP servers** — the protocol surface: discoverable
tools the platform can compose.

**Observability** — OTel GenAI semantic conventions, Langfuse, LangSmith,
Arize Phoenix: the capture layer.

**Evaluation** — benchmark harnesses and eval frameworks (Inspect,
DeepEval, Promptfoo): the scoring layer.

## Why six and not more

Six because each answers a question a production team actually asks
(where does it run, what does it know, how do I see it, how do I score
it). The count is a diagnostic, not a law — the point is that a
production agent needs all six, and most teams under-provision the
sandbox and evaluation layers.

## What this does not say

It does not claim one vendor owns the stack — the layers are
best-of-breed territory. It maps the machine room the platform stages sit
on.
