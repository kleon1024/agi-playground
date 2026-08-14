---
status: draft
level: reference
label: When the agent runs itself
---

# Meta-agents, self-extension, and the governance line

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** the far end of autonomy is the agent that writes its own
tools, skills, or subagents. The industry has demonstrated it — 16 parallel
Claude agents built a working C compiler under \$20K with humans holding
the core decisions ([DoNews write-up, 2026-07](https://www.donews.com/news/detail/4/6652405.html)).
Where does self-extension stop being a demo and become a governance
problem?

## What self-extension looks like

Agents already extend themselves inside bounds: Claude Code writes
dynamic-workflow orchestration scripts that spawn subagents (used for
monorepo-wide migrations); Cursor's skills graduate into automations; pi's
coding agent is described as self-extensible. The governance-relevant
step is when the agent changes the instructions, tools, or permissions
that govern its own future runs.

## The governance line

NVIDIA's invariants name the line: no self-granted authority, no
agent-created persistence, no agent-controlled lifecycle. An agent may
write code; it may not widen its own policy, persist its own shell
hooks, or change its own sandbox. The mission's guardrail is the same
line at mechanism scale — a patch that edits its own test file is
scored as tampering.

## Why this sits beside the authorization matrix

Self-extension is where the matrix's Level 5 row lives: orchestration with
minimal oversight. The matrix grants it only where the objective is
measurable, the tools are scoped, progress is checkpointed, and stop
conditions are explicit — the four properties Cursor's five-day
hill-climbing runs met.

## What this does not say

It does not claim self-extension should be banned — it is where the field
is going. It maps the line where a capability becomes a governance
decision, which is the control-plane stage's invariant territory.
