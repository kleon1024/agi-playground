---
status: draft
level: frontier
label: Control plane and governance
---

# The agent sees a sandbox. Who sees the agent?

**Question:** every layer so far made the agent more capable. This stage
makes the fleet governable. A control plane is the active layer between
observability (which tells you what happened) and the agent (which keeps
doing it): it enforces policy, blocks sensitive actions, holds budgets, and
keeps an audit trail. The category barely existed at the start of 2026 and
had four credible products by mid-year. What does a platform actually
govern, and what are the invariants?

**The artifact this stage follows** is the platform map: every stage of this
topic drawn as a plane (execution, context, tools, verification, control),
with the mission's recorded runs placed on it — one diagram that shows where
each verified number lives in the platform.

By the end you will be able to take any agentic platform (OpenAI's
three-layer stack, a control-plane product, NVIDIA's reference
architecture) and say which plane owns which decision, and which invariant
it enforces.

**Before this:** stages 07–11 built the platform's capabilities. This stage
is the layer that governs them all, and it feeds the autonomy decision in
[stage 15](../autonomy-and-orchestration/).

## What this stage decides

What the agent may do without asking, and who can change that. The control
plane's decision is policy — routing, budgets, sensitive-action blocking,
audit — and the invariant set that makes policy enforceable (no
self-granted authority, no agent-controlled lifecycle, no suppressed audit).

## Planned chapters

- **[the-platform-layers](the-platform-layers/)** — the industry's layered maps compared: TokenJam's
  nine-layer ecosystem (observability, evaluation, environments, gateways,
  memory, guardrails, human-in-the-loop, control plane, optimization),
  OpenAI's three-layer stack (SDK / Responses API / AgentKit), NVIDIA's
  seven-plane reference.
- **[control-vs-observability](control-vs-observability/)** — the passive/active split and why it
  surfaces only at incidents; the 2026 control-plane products (Galileo
  Agent Control, Salesforce Agent Fabric, Microsoft Agent 365, HumanLayer
  ACP) and the two underbuilt layers (optimization, dev-first control
  planes).
- **[the-enterprise-matrix](the-enterprise-matrix/)** — the five vendor platforms (AWS Bedrock
  AgentCore, Microsoft Copilot Studio, Google ADK, OpenAI AgentKit, and
  Anthropic) with their orchestration primitives, and A2A as the
  agent-to-agent protocol binding them.
- **[no-secrets-no-authority](no-secrets-no-authority/)** — NVIDIA's invariants made concrete: the
  credential proxy (agent receives capabilities, never raw tokens),
  deny-by-default egress, no agent-created persistence, and what each
  invariant defends against.
- **our-platform-map** (recorded diagram) — the topic's own stages drawn as
  the platform planes, with every verified run placed on the plane that
  owns its evidence; the diagram is a ProcessDiagram, not a new Mermaid.

## Evidence strategy

All chapters are dated surveys; `our-platform-map` reuses already-recorded
runs and is a reading/diagramming exercise, not new measurement.

## Industrial grounding

TokenJam's 2026 map: the control-plane category did not exist at the start
of 2026 and had four credible products by mid-year. OpenAI's AgentKit 1.0
(2026) is a hosted agent runtime owning loop, memory, and deploy. NVIDIA's
Secure Agent Workspace reference enumerates the invariants — no raw
credentials, no self-granted authority, no agent-controlled lifecycle, no
suppressed audit — and explicitly notes the future shape: the agent moves
to a separate control plane and the workspace becomes a pure tool-execution
sandbox.
