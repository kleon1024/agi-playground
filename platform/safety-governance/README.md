---
status: draft
---

# Platform — Safety and governance

**Goal:** the guardrails a mission declares must be enforceable by something,
and this is that something.

## Why this is a platform layer, not a topic

Safety appears in most curricula as a chapter: alignment techniques, red
teaming, refusal behaviour. Useful, but it treats safety as a property of a
model. In a system that makes decisions for a stakeholder, most of what can go
wrong is not the model saying something bad — it is the system doing something
bad, or doing something reasonable to the wrong person, or being unable to
explain what it did.

Every mission contract declares `guardrails`: what must not degrade. That
declaration is worthless without a layer that can measure and enforce it, which
is why this sits beside data, training, serving, and evaluation rather than at
the end of the curriculum.

## Scope

- **Guardrail measurement** — turning a declared constraint ("diversity must not
  regress", "no PII in output") into a check that runs alongside the primary
  metric.
- **Permission and blast radius** — what a system is allowed to do
  autonomously, and what a failure can reach. Shares ground with
  [`capabilities/act-coordinate`](../../capabilities/act-coordinate/), which
  covers the harness-level mechanics.
- **Provenance and auditability** — being able to say why a decision was made,
  which is a hard requirement in ranking, credit, and health contexts and a
  soft one everywhere else.
- **Data governance** — consent scope, retention, and the difference between
  "we have this data" and "we may use it for this purpose".
- **Failure cataloguing** — the mission contract requires failure analysis; the
  discipline of collecting and classifying failures lives here.

## Status

Not yet built. It becomes real when the second mission declares guardrails that
need enforcing — a recommendation mission with diversity and fairness
constraints is the natural forcing function, since those are exactly the
guardrails that a naive primary metric will happily trade away.

Mission 01 does not exercise this layer, which is itself worth noting: a
single-user, local, text-only system has almost no blast radius. That is why it
is a poor test of safety machinery and a good first integration test.
