---
status: draft
level: reference
label: Reading Cursor and open harnesses
---

# Editor-first and open harnesses, read as five decisions

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** Claude Code and Codex are terminal-first. Cursor is
editor-first, and the open harnesses (OpenHands, SWE-agent) are
research-first. Do they fill the five decisions differently in kind, or
only in default?

## Cursor's answers

**Loop.** In-editor agent mode plus cloud background agents that run async
in isolated VMs on a branch and return a PR
([Cursor docs](https://cursor.com/docs)).

**Sandbox.** Cloud agents run in isolated VMs, and the editor surface keeps
the human closer to each edit than a terminal agent does — the approval
posture is the product difference.

**Verification as a first-class plane.** Cursor's agent factory adds what
the other harnesses treat as external: CI, security review, risk scoring,
behavioral evidence (demo recordings attached to PRs), and a review agent
(Bugbot) whose mistakes become future eval cases
([Arize Observe 2026 write-up](https://arize.com/blog/inside-cursors-agent-factory-how-it-verifies-ai-written-code/)).
The verification-and-evals stage's evidence-contract chapter develops
this.

## The open harnesses

OpenHands and SWE-agent are the research harnesses that made agent
benchmarks measurable; they fill the same five decisions with
research-grade defaults (explicit context budgets, reproducible tool
sets). They matter here as the disclosure baseline: when a paper reports
a score, the harness is open and inspectable — the exact property the
stage's "disclose the harness" warning asks for.

## Why this chapter exists

The five-decision reading collapses three product families into one
comparison table, which is the point: the harness is the independent
variable, and editor-first, terminal-first, and research-first are
defaults on the same five axes, not different species.

## What this does not say

It does not rank the harnesses — the mission's runs show defaults carry
costs, and the right posture is per-team. It provides the reading.
