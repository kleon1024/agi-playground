---
status: draft
level: reference
label: The platform layers
---

# Three maps of the agentic platform

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** the stage claims an agentic platform is a set of planes, and
the industry has published three overlapping maps. Reading them side by
side is the fastest way to see where the platform's real boundaries are.

## The three maps

**TokenJam's nine layers** (2026-05) — observability, evaluation,
environments, gateways, memory, guardrails, human-in-the-loop, control
plane, optimization. Two layers were underbuilt: optimization (no product
owner) and the dev-first end of the control plane
([map](https://tokenjam.dev/blog/2026-05-26-the-9-layer-agent-ecosystem-map)).

**OpenAI's three layers** — Agents SDK (orchestration), Responses API
(runtime), AgentKit (deployment/control plane with visual builder,
Connector Registry, ChatKit)
([AgentKit](https://openai.com/index/introducing-agentkit/)).

**NVIDIA's seven planes** — the Secure Agent Workspace reference: agent
loop, runtime sandbox, single-user workspace VM, and the workspace
envelope, with six architectural invariants
([reference](https://docs.nvidia.com/enterprise-reference-architectures/secure-agent-workspace-reference-design/latest/reference-architecture.html)).

## What the maps agree on

The maps disagree on count and agree on substance: execution and control
are separate planes, observability is passive while the control plane is
active, and the layer count rises with autonomy — a team running one
bounded agent needs observability; a fleet needs a control plane.

## What this means for this topic

The topic's 19 stages are a decomposition of these maps: execution
environment and runtime are the environments plane; context/memory and
tools are the memory and gateway planes; verification is the evaluation
plane; control-plane-and-governance is the control plane; autonomy is the
human-in-the-loop plane; infrastructure is the substrate.

## What this does not say

It does not claim any map is canonical — the counts are arbitrary; the
questions they answer are not. It uses the maps to locate the topic's
stages.
