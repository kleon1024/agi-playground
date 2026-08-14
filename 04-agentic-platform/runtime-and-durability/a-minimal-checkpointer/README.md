---
status: verified
level: applied
base: scratch
label: A minimal checkpointer
verified: 2026-08-14
---

# The task survives the crash, step by step

**Question:** the stage claims a long task must survive a crash — state is
written somewhere resumable, and a killed process restarts from the
checkpoint instead of from zero. Can that be demonstrated in a file small
enough to read in one sitting?

**The artifact this chapter follows** is the checkpoint record: two real
task ids, one simulated crash, one resume — and the count that proves the
resumed step was not redone.

By the end you will be able to say what a checkpoint must store (completed
work, not just position), and where a file-level checkpoint stops being
enough and a durable execution engine takes over.

**Before this:** the stage's resumability claim. This chapter is its
smallest working instance.

## The record, read

```text
run 1:  [done]    private-b81c414 -> 1dde1588e568
        [crash]   simulated crash before step 1 (private-354c352)   exit=3
run 2:  [resumed] private-b81c414 already done
        [done]    private-354c352 -> feb10d2d8284

all 2 steps complete; attempts=3 (resumed steps are not redone)
```

The checkpoint stores the set of completed steps, not the loop position.
That distinction is the whole point: a position-based checkpoint loses
work if the crash happens mid-step, while a completed-work checkpoint is
idempotent by construction. Resuming replays only what is unfinished —
which is exactly what Temporal and Restate formalize with journal replay
and idempotency keys at a scale this file only gestures at.

## What this proves and what it does not

It proves the mechanics: crash, checkpoint, resume, no-redo, all recorded
with the same honesty contract as every other run. The work per step is
deliberately trivial so the demo isolates durability from task difficulty.

It does not prove a production agent can checkpoint its own conversation —
context, tool history, and plan state are harder than a set of task ids.
The stage's surveys cover how durable execution engines persist *every*
LLM call and tool result; this chapter proves the shape, not the scale.

**Next:** [checkpoint-and-resume](../) — where a file checkpoint is enough
and where it is not.
