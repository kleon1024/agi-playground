---
status: draft
level: reference
label: Checkpoint and resume
---

# Where a file checkpoint is enough, and where it is not

> Dated survey, 2026-08-14.

**Question:** the demo checkpoints a set of completed task ids. When is
that shape enough, and when do you need a real durable execution engine?

## When a file checkpoint is enough

When the work is **idempotent and coarse-grained**: each step's side
effects are repeatable, and the state that matters is a small set of
completed units. The mission's task dispatch is exactly this shape — a
resumed run re-does nothing, and the checkpoint is a list. Many
scheduled/background agent workloads (CI repair, dependency bumps) are
also this shape.

## When it is not enough

When the state is **conversational or interleaved**: the plan depends on
earlier tool results, side effects cannot be replayed safely, or steps
have partial effects on shared state. A file of completed ids cannot
reconstruct the reasoning that produced the next step. That is the
durable-execution chapter's domain — journal every call, replay with
idempotency keys.

## The deciding question

"Can a resumed run produce a different result than a fresh run with the
same checkpoint?" If yes, the checkpoint is insufficient. The demo's
steps are pure functions of their inputs, so it passes; a plan-gated
workflow whose next step depends on conversation history does not.

## What this does not say

It does not claim file checkpoints are production durability. It draws
the line the stage's surveys make operational: checkpoint what you can
prove idempotent, and hand the rest to an engine.
