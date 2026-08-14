---
status: draft
level: frontier
label: Runtime and durability
---

# What happens to the task when the machine dies?

**Question:** stage 03's loop lives in one process. A production agent runs
for hours, in a sandbox that can crash, be preempted, or lose its session —
and every LLM call, tool result, and decision is state that has to survive.
The industry answer is durable execution: persist every step so the agent
resumes where it stopped instead of restarting. What does that take?

**The artifact this stage follows** is a checkpoint: the agent's full state
— loop position, tool history, context — written to a store it can resume
from, plus a recorded run that kills the process mid-task and resumes.

By the end you will be able to read any durable execution platform
(Temporal, Restate, Durable Objects, a checkpointed harness) as the same
three guarantees — state persists, execution resumes, nothing runs twice —
and say which one a given system actually provides.

**Before this:** [stage 07](../execution-environment/) isolated where the
agent runs. This stage makes the isolated run survivable, and it feeds the
orchestration decisions in [stage 11](../orchestration-and-workflows/).

## What this stage decides

Whether a long task is resumable, idempotent, or restartable. The decision
matters exactly when autonomy climbs: an agent that runs unattended for
hours is only as trustworthy as its ability to survive a crash without
corrupting its own progress.

## Planned chapters

- **[when-the-task-dies](when-the-task-dies/)** — the failure taxonomy of long-running agents:
  crash, preemption, session loss, timeout; what state exists at each point
  and what "restart" means when the state is a conversation.
- **[durable-execution](durable-execution/)** — Temporal, Restate, and Durable Objects as the
  three production answers; journal replay, idempotency keys, and why
  Thoughtworks' radar lists "ignoring durability in agent workflows" as a
  trap.
- **[checkpoint-and-resume](checkpoint-and-resume/)** — the lightweight version: checkpointing a
  harness's state to disk or SQLite; where a checkpoint is enough and where
  you need a real durable execution engine.
- **[a-minimal-checkpointer](a-minimal-checkpointer/)** (local mechanism demo) — add checkpoint/resume
  to the stage 03 loop, kill the process mid-task, and record the resume in
  `runs/`.

## Evidence strategy

`a-minimal-checkpointer` is the only run; it reuses stage 03's harness and
task set. The rest are dated surveys of documented platforms, with the
Thoughtworks radar and vendor docs cited inline.

## Industrial grounding

Temporal, Restate, Inngest, and DBOS all achieve durability through journal
replay; Cloudflare's agent runtime puts every agent on a Durable Object —
a stateful micro-server with its own SQL store — and Anthropic's Claude
Managed Agents run on sandboxes whose sessions keep state across inactivity.
Thoughtworks' 2026 radar flags ignoring durability in agent workflows as a
technique to avoid.
