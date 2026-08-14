---
status: verified
level: applied
base: scratch
label: A minimal planner
verified: 2026-08-14
---

# The plan as a contract, generated from the mission's real tasks

**Question:** the stage claims a plan is a contract — exact file paths,
exact tests, an exact verification command — grounded in facts the agent
discovered, not guesses it asked about. What does that contract look like
for a real task, and what does it deliberately not claim?

**The artifact this chapter follows** is the plan output for both of the
mission's private tasks: grounded, reviewable, and honest about its own
limits. No model was called — the planner is rule-based, which is the
point: the *shape* of a plan is separable from the intelligence that fills
one.

By the end you will be able to read any production planning flow (Codex
plan mode, Jules, a spec-driven repo) as the same moves this chapter's
planner makes mechanically.

**Before this:** the stage's plan-as-contract claim. This chapter is its
smallest working instance.

## What a plan must contain

The planner turns a task record into four explicit sections:

- **Files to change** — exact paths, from the record's `source_files`.
- **Tests this must satisfy** — exact test files, from `target_tests`.
- **Verification** — the exact command that decides done, from
  `test_command`.
- **What the plan does not claim** — it does not claim the fix; the test
  decides that, and the ground truth stays in the task record, not the
  plan.

The plan for `private-b81c414` reads:

```text
# Plan: attend past the first token in every cached decode step
Files to change      missions/01-language-model-agent/05-serve/core/engine.py
Tests to satisfy     tests/test_decode_correctness.py
Verification         uv run --group torch pytest -q tests/test_decode_correctness.py
```

Every field traces to the task record. Nothing is invented, and nothing is
left to be discovered at execution time — which is exactly the property
that makes a plan reviewable by a human before any tool runs.

## What this proves and what it does not

It proves the contract shape: grounding, exactness, and an explicit
non-claim boundary are mechanical, not magical. The stage's argument that
vague tickets produce vague output and review cycles is made concrete here —
a planner that refused to invent file paths is a planner that cannot
produce a vague plan.

It does not prove a plan improves resolve rate. That is the mission's
empirical question, and it has not been run against the plan-gated
workflow. This chapter establishes the artifact; the measurement is a
planned run, not a claimed result.

**Next:** [the plan-as-contract](../) — the approval gate that sits between
this plan and execution.
