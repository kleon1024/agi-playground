---
status: draft
level: reference
label: The plan as contract
---

# The approval gate between plan and execution

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** the plan is only a contract if someone signs it. What does
the approval gate look like in production, and what makes a plan
approvable?

## What makes a plan approvable

**Exactness** — file paths and structures, not intentions: Codex's plan
mode requires exact paths, structures, and signatures; the mission's
planner refuses to invent them.

**Boundedness** — a plan that can be reviewed in minutes: TL;DR
checkpoints and plan-only outputs keep the review cost near zero.

**Durability** — the plan survives execution and is the artifact the
result is measured against: the spec-driven pipeline's verify phase.

## The gate

The approval gate is the human-control unit: the agent proposes, the human
approves, rejects, or redirects before any edit
([Tembo's gate-first principle](https://www.tembo.io/blog/autonomous-coding-agents)).
It costs seconds when the agent is right and saves an incident when it is
wrong.

## What this means for this topic

The mission's routing decision starts from a task; this chapter closes the
loop by making the task's plan the artifact the routing approves. The
plan-as-contract is where intent becomes a decision the authorization
matrix can price.

## What this does not say

It does not claim every task needs a heavyweight spec — the review cost
must be proportional to the change. It maps what makes a plan approvable
and where the gate sits.
