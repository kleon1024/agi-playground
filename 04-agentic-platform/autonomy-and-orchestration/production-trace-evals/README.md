---
status: draft
level: reference
label: Production trace evals
---

# The eval that feeds the next decision, not the next dashboard

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** the verification stage scores agents. Production trace eval
is the version that closes the loop: production traces feed evaluation,
evaluation feeds policy, policy feeds the control plane. What is the
wiring?

## The wiring

OpenTelemetry GenAI semantic conventions give traces a shared schema
(spans for model calls, tool invocations, and agent steps), and the
observability platforms (Langfuse, LangSmith, Arize Phoenix, Braintrust)
all ingest them
([observability comparison](https://dev.to/gabrielanhaia/langfuse-vs-langsmith-vs-phoenix-vs-braintrust-the-honest-2026-comparison-253p)).
The step that turns traces into decisions is scoring: offline eval on
recorded traces, CI gates on new runs, and production evaluation where
`gen_ai.evaluation.score` attaches a score to a live span.

## The loop Cursor runs

Observe → evaluate → diagnose → improve → deploy: an eval failure emits a
trigger, launches a diagnosis workflow with the trace context attached,
and the result updates the rules, skills, or eval set. That is the
"self-driving" version — detection is wired to action, not to a dashboard
([Arize write-up](https://arize.com/blog/inside-cursors-agent-factory-how-it-verifies-ai-written-code/)).

## What this means for this topic

The mission's runs are traces in miniature — every verdict records the
path that produced it, and the a-minimal-judge demo replays recorded
verdicts through scorers. Production trace eval is that pattern at fleet
scale, and it is the tuning mechanism for the authorization matrix.

## What this does not say

It does not claim traces alone improve agents — a score must feed a
control decision, not a report. It maps the wiring that makes eval
operational.
