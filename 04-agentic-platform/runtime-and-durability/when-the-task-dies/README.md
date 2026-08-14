---
status: draft
level: reference
label: When the task dies
---

# Crash, preemption, session loss: what state is at stake

> Dated survey, 2026-08-14.

**Question:** the stage's demo checkpoints a task id set. A production
agent's state is richer: the conversation, the tool history, the plan, the
working tree. When the machine dies, what exactly is lost, and what does
"restart" even mean for each kind of state?

## The state that can be lost

**Conversation state** — the loop position, the reasoning so far, the
tool results already gathered. Restarting from zero re-does every call;
that is the cost the checkpointer demo's `attempts` counter measures in
miniature.

**Tool side effects** — files written, packages installed, services
started. These survive in the sandbox but not in the conversation; a
restart that replays the conversation without re-applying side effects
produces a confused agent. This is why durable execution journals *tool
calls*, not just messages.

**Plan state** — the spec-driven plan from the intent stage, half
executed. A crash mid-plan is the worst case: the agent knows where it
was, the filesystem knows what it did, and nobody has the mapping.

**Identity and permission** — what the agent was authorized to do. A
resumed agent that lost its delegation record must not silently regain
authority; NVIDIA's invariants make revocation part of the lifecycle.

## Why this taxonomy matters

The industry's durable execution engines exist because the conversation
is the least durable part of an agent. Restarting a conversation is
possible; restoring a half-applied plan with the right permissions is an
engineering problem. The taxonomy is the precondition for choosing a
mechanism — the next chapter's durable-execution survey.

## What this does not say

It does not prescribe one mechanism. It names the state at stake so the
checkpoint chapter's "what to persist" question has an answer set.
