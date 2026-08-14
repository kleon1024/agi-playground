---
status: draft
level: reference
label: AgentFS and persistent workspaces
---

# State that lives beyond the context window

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** context windows are bounded; work is not. Persistent
workspaces — filesystem- or database-backed state that outlives any single
session — are how long-running agents keep working. What are the shapes?

## The shapes

**AgentFS** exposes agent state (memory, tasks, tool results) as a POSIX
filesystem, so an agent's native file tools reach state without custom
APIs ([AgentFS](https://github.com/knite51/agentfs)).

**BranchFS workspaces** give exploration a fork-and-commit lifecycle:
O(1) copy-on-write branches, atomic commit-to-parent
([BranchFS](https://github.com/rewrite-the-world/branchfs)).

**Cloud persistent sessions** — Claude Managed Agents keep session state
across inactivity on sandboxes; Codex Cloud and Jules clone and work on
persistent branches. The runtime stage's durability is the same idea at
the execution layer.

## Why persistent state is a platform property

The context window is the wrong place for a task that spans hours:
compression loses the exact values that make work actionable. A
persistent workspace holds the state, and the agent retrieves only what
the current step needs — the two-layer memory split applied to work, not
just facts. The mission's checkpointer demo is the smallest form: the
completed-work set survives the crash.

## What this does not say

It does not claim filesystems replace vector memory or databases — each
holds a different kind of state. It maps the workspace shape and why the
industry moved sessions from ephemeral to persistent.
