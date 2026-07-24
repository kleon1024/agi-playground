---
status: draft
---

# 07 — Evals

## Scope

Evaluating models and agents honestly: standard benchmark harnesses
(perplexity, task suites), and the harder, less-served problem of
harness-aware agent evaluation — recognizing that harness design (loop, tools,
context management) is itself an independent variable in agent benchmark
results, not a footnote.

## Prerequisites

None strictly required to start — evals can run against any checkpoint or
agent. In practice this track is most useful once you have a model from
`03-pretraining` (or later) and/or an agent harness from `08-agents` to
evaluate.

## Planned lessons

1. `01-perplexity-and-lm-eval-harness` — standard language-model evaluation,
   perplexity and task-suite scoring via lm-eval-harness.
2. `02-task-suites-with-inspect-ai` — structured eval design with inspect-ai.
3. `03-harness-disclosed-agent-evals` — why agent benchmark comparisons need
   to disclose harness design (loop, tools, context management) as an
   independent variable, not hide it.
4. `04-building-an-eval-report` — assembling an honest, reproducible eval
   report across model and agent evaluations.

## Speedrun note

`04-building-an-eval-report` is the seed lesson for speedrun stage
`07-eval` — the final integration report across perplexity, task suite, and
harness-disclosed agent eval for every prior stage.
