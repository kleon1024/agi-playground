---
status: draft
level: reference
label: Spec-driven orchestration
---

# The issue tracker becomes the skeleton

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** the workflow skeleton needs a home. The 2026 answer: the
issue tracker. Spec-driven orchestration derives the skeleton from a
spec, dispatches agents from a backlog, and turns ticket quality into a
direct productivity input. How does it work?

## The pattern

**Spec-in, PR-out.** A spec is written first — exact files, exact
structures, acceptance criteria — and the agent executes against it. The
plan is the contract the intent-to-plan stage teaches; orchestration
scales it across a backlog.

**Symphony** (OpenAI, 2026-04) — an open spec for orchestrating many Codex
agents from an issue tracker: every open task gets an agent, agents run
continuously, PRs return for review
([Symphony spec](https://rywalker.com/research/openai-skills)).

**GitHub Spec Kit** (2026) — an 8-phase pipeline (constitution → spec →
plan → execute → verify) compatible with 30+ coding agents
([Spec Kit](https://github.com/github/spec-kit)).

## Why ticket quality is a productivity input

Spec-in/PR-out amplifies whatever is in the spec: a vague ticket produces
vague output and more review cycles than the automation saved. OpenAI's
own stack documentation makes the organizational point — the humans write
specs and design gates; the agents execute
([Code agent stack analysis](https://www.joinnextdev.com/blog/openais-code-agent-stack-changes-the-buy-vs-build-calculus)).

## What this means for this topic

The intent-to-plan stage establishes the spec as contract; this chapter
scales it into orchestration. The mission's task set is a spec-shaped
artifact already — a failing test is an acceptance criterion.

## What this does not say

It does not claim spec-driven development is easy — spec discipline is a
human skill the industry is hiring for. It maps the pattern and why the
industry converged on it.
