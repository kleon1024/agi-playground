---
status: draft
level: reference
label: Control vs observability
---

# Watching is not the same as stopping

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** observability and the control plane look similar until an
incident. The distinction is direction: observability is passive and tells
you what happened; a control plane is active and stops things from
happening. Why does that difference surface only in the incident?

## The distinction

Observability records: model calls, tool invocations, tokens, costs,
reasoning chains — the capture layer
([TokenJam](https://tokenjam.dev/blog/2026-05-26-the-9-layer-agent-ecosystem-map)).
A control plane enforces: policy, budget caps, sensitive-action blocking,
audit trails — it can halt an agent that keeps producing bad output.

## The 2026 products

The category barely existed at the start of 2026 and had four credible
entrants by mid-year: Galileo Agent Control (open source), Salesforce
Agent Fabric, Microsoft Agent 365, and HumanLayer ACP. They are
enterprise-first — the gap the map notes is a dev-first control plane.

## Why this topic needs the split

The mission's guardrail is a control-plane mechanism: it halts a patch
that touches a test file, it does not just log it. The governance runs in
verification-and-evals are the record of that active layer. Reading a
production agent's safety as "we log everything" is the category error
this chapter exists to prevent.

## What this does not say

It does not claim control replaces observability — a control plane with no
observability is flying blind. It maps the active/passive split and why
the incident is where the difference shows.
