---
status: draft
level: frontier
base: none
label: Runtime and durability
---

# The process will die. What survives it?

**Question:** the mission's agent takes 7–19 turns and 60–200 seconds per
task — and the recorded runs show attempts that hit the wall-clock cap and
produced nothing. Those attempts cost real dollars and returned zero. A
crash, a preemption, a lost session does the same: every LLM call, tool
result, and decision is state, and if that state dies with the process,
the agent restarts from zero and re-pays the whole task. What exactly has
to survive, and how do you prove nothing was redone?

**The artifact this stage follows** is [a-minimal-checkpointer](a-minimal-checkpointer/),
a real recorded run that kills the process mid-task and resumes it
([record](a-minimal-checkpointer/runs/2026-08-14-checkpointer.md)). The
counter that proves the resumed step was not redone is the spine of this
stage: every durable execution platform below is that counter, at scale.

**Before this:** [stage 07](../execution-environment/) isolated where the
agent runs. This stage makes the isolated run survivable.

## The failure, priced in this mission's own numbers

The mission's model-tier record ([stage 05](../cheap-or-expensive/)) shows
what a dead attempt costs: two of three sonnet attempts on `b81c414` hit
the declared 240-second cap and produced nothing at all. A timeout is a
death, and the dead attempt is not free — it burned context and wall-clock
before dying. Now scale that to a production agent that runs for hours
instead of minutes, and "the process will die" stops being a hypothetical.
Cloud preemption, session expiry, and crashes are not exceptional; they are
the operating conditions.

## What has to survive: the state taxonomy

Before choosing a mechanism, name what is at stake. A production agent's
state is four kinds, and they do not die equally
([when-the-task-dies](when-the-task-dies/)):

| State | What it is | What "restart" means for it |
|---|---|---|
| Conversation | loop position, reasoning, tool results gathered | redo every call — the cost the demo's `attempts` counter measures |
| Tool side effects | files written, packages installed, services started | survive in the sandbox but not in the conversation; replaying the conversation without re-applying them produces a confused agent |
| Plan state | the spec-driven plan, half executed | the worst case: the agent knows where it was, the filesystem knows what it did, nobody has the mapping |
| Identity and permission | what the agent was authorized to do | a resumed agent that lost its delegation must not silently regain authority |

The first row is why the industry answer is not "restart the conversation":
restarting a conversation is possible, restoring a half-applied plan with
the right permissions is an engineering problem.

## The mechanism: persist completed work, not position

The demo's distinction is the whole mechanism. A checkpoint can store the
loop *position* — "I was at turn 8" — or the set of *completed work*. The
position version loses everything after the last checkpoint if the crash
hits mid-step. The completed-work version is idempotent by construction:
resuming replays only what is unfinished, and redoing an already-done step
is impossible because it is not in the unfinished set.

[a-minimal-checkpointer](a-minimal-checkpointer/) shows it in a file small
enough to read in one sitting:

```text
run 1:  [done]    private-b81c414 -> 1dde1588e568
        [crash]   simulated crash before step 1 (private-354c352)   exit=3
run 2:  [resumed] private-b81c414 already done
        [done]    private-354c352 -> feb10d2d8284

all 2 steps complete; attempts=3 (resumed steps are not redone)
```

The `attempts=3` line is the claim: the resumed run did not redo
`b81c414`, and the count says so. `b81c414 already done` is not a log
message, it is the checkpoint refusing to replay finished work.

## Where a file checkpoint stops being enough

The demo checkpoints a set of task ids. A production agent's state is the
four-kind taxonomy above, and persisting *conversation plus side effects*
is where the lightweight approach breaks. If you persist the conversation
but not the tool side effects, a replay makes tool calls the agent already
made — installing packages twice, applying edits twice, paying for
inference twice. If you persist side effects but not the conversation, the
resumed agent has a filesystem it does not understand.

That is what durable execution engines formalize
([durable-execution](durable-execution/)): Temporal, Restate, and
Cloudflare's Durable Objects journal *every step and every tool call*, and
replay the journal with idempotency keys — the same "completed work, not
position" rule the demo implements in 100 lines, generalized so a call
that succeeded once is never made twice. The industry signal is blunt:
Thoughtworks' 2026 radar flags *ignoring durability in agent workflows* as
a technique to avoid, which is the same sentence as "let the process die
with the state."

The practical line between the two is [checkpoint-and-resume](checkpoint-and-resume/):
a file checkpoint is enough when the state is small, resumable, and
idempotent — the mission's task set is exactly that. A durable engine is
required when the state is a long conversation with side effects that
cannot be replayed cheaply.

## What this stage does and does not establish

It establishes the mechanism: the completed-work invariant, the
`attempts` counter that proves no redo, and the line where a file
checkpoint gives way to journal replay. The mechanism is verified by the
recorded crash-and-resume run; the production claims are dated surveys
with sources cited.

It does not claim the demo can checkpoint a real agent's conversation —
the four-kind taxonomy is exactly what a task-id set cannot represent, and
the chapter says so instead of blurring the boundary. And it does not
claim durability makes a task cheap to resume: it makes resumption
*possible*, which for a crashed attempt is the difference between a
refund and a second bill.

**Next:** the task survives, but the agent still forgets — context and
memory are the next thing the platform has to add
([context-and-memory](../context-and-memory/)).
