---
status: draft
level: reference
label: Agentic DevOps
---

# Running the machine room: rollout, canary, incident response for agents

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** agents that run unattended need operations, not just
deployment. What does the ops loop look like when the workload is an
agent — and how does observability feed the next decision?

## The ops loop

The pattern Cursor described (Arize Observe 2026): observe, evaluate,
diagnose, improve, deploy. An eval failure emits a trigger, launches a
diagnosis workflow with trace context already attached, and the result
updates the rules, skills, or eval set
([write-up](https://arize.com/blog/inside-cursors-agent-factory-how-it-verifies-ai-written-code/)).
That is the "self-driving" ops loop: detection is wired to action, not to
a dashboard.

## What changes at fleet scale

At one agent you remember what you asked for; at fifty you need a record —
who dispatched what, against which repo, with which approval, and what
the diff was. Orchestration, isolation, and governance become the
operating concerns ([Tembo's scale analysis](https://www.tembo.io/blog/autonomous-coding-agents)).
CI speed becomes a throughput bottleneck when agents open parallel
branches faster than the test suite runs ([code-agent-stack analysis](https://www.joinnextdev.com/blog/openais-code-agent-stack-changes-the-buy-vs-build-calculus)).

## Why this belongs in the infrastructure stage

The ops loop is the platform's feedback mechanism: production traces feed
evaluation, evaluation feeds policy, policy feeds the control plane. The
topic's production-trace-evals chapter develops the evaluation side; this
chapter is the ops side that runs it.

## What this does not say

It does not claim agents replace SRE — humans stay on policy, escalation,
and deployment approval. It maps the loop and the scale effects.
