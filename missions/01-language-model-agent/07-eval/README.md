---
status: draft
---

# Speedrun 07 — Eval

## Goal

Close the loop with one honest, reproducible evaluation report covering every
prior speedrun stage.

## Deliverable

Perplexity evaluation, a small task-suite score, and a harness-disclosed
agent evaluation, combined into one report.

## Anchor project

lm-eval-harness, inspect-ai (see `platform/evaluation-observability/LANDSCAPE.md` for the
toy/production mapping). Seed lesson: `platform/evaluation-observability/README.md`,
`04-building-an-eval-report`.

## Verification criterion

No verified run yet — depends on `06-agent` landing first (and, for the
model-level evals, on `02-pretrain`/`03-sft`/`04-rl`). When run, its `runs/`
entry must show: the exact eval commands for each component (perplexity,
task suite, agent eval), the harness configuration disclosed alongside the
agent-eval numbers, and a single report a newcomer can reproduce end-to-end
by following only this repo's docs.
