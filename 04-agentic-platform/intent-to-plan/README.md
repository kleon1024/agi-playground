---
status: draft
level: frontier
label: Intent to plan
---

# A bug report is not a task. What has to happen between them?

**Question:** the mission's task set assumes the intent is already
unambiguous — a failing test that says what correct looks like. Real work
never arrives that way: a ticket, a chat message, or a sentence about a
feature is vague, and an agent that executes a vague intent produces vague
output and review cycles that cost more than the automation saved. What
does the industry actually put between "intent" and "execution"?

**The artifact this stage follows** is the plan as a contract: a durable,
reviewable document that a human approves before any tool runs, and that the
agent is later measured against. The stage's decision is where intent
becomes a plan, and who signs it.

By the end you will be able to read any production planning flow (Codex plan
mode, Jules, GitHub Spec Kit, a spec-driven repo) as the same three moves —
ground the intent in facts, write the plan as an exact artifact, gate it
behind human approval — and say which of the three your own harness is
missing.

**Before this:** [stage 00](../task-set/) defined what makes a task
scorable. This stage adds the step the task set skipped: converting a fuzzy
request into that scorable form without losing the requester's meaning.

## What this stage decides

The routing decision in [stage 05](../cheap-or-expensive/) starts from a
task. This stage decides what must be true of that task before routing is
meaningful: the intent is grounded, the plan is exact, and a human has
signed it. A harness that skips this stage optimizes the wrong thing — it
measures resolve rate on tasks nobody actually asked for.

## Planned chapters

- **when-the-request-is-vague** — what one ambiguous ticket costs when an
  agent executes it, and how production flows (Codex plan mode's grounding
  rule "discover facts, not by asking the user", Jules's clone-then-plan)
  force intent into a checkable form before any edit.
- **spec-driven-development** — GitHub Spec Kit (2026, open source, 30+
  compatible agents) and the 8-phase pipeline; why spec-first became the
  industry answer to "vague tickets produce vague output".
- **the-plan-as-contract** — plan-only outputs (exact file paths, exact
  structures), TL;DR checkpoints, and the approval gate as the unit of
  human control; the plan as the artifact the agent is later scored against.
- **a-minimal-planner** (local mechanism demo) — a 200-line planner that
  takes the mission's six real tasks, forces a plan-only step, and records
  what changes in resolve rate when the plan is reviewed before execution.

## Evidence strategy

The three survey chapters are dated reference material with inline sources;
no number in them is measured here. `a-minimal-planner` is the only runnable
piece: it reuses the mission's existing task set and harness, so its run is
recorded in `runs/` with the same command/hardware/metrics contract as every
other stage.

## Industrial grounding

OpenAI's plan mode requires the final plan to be plan-only and grounded in
discovered facts. Google's Jules clones the repository, drafts a plan for
approval, then returns a diff. GitHub's Spec Kit made spec-driven
development a standard workflow across 30+ coding agents in 2026. The
common shape is the same one this stage teaches: intent → grounded plan →
human gate → execution.
