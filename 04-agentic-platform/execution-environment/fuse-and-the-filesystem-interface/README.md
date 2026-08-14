---
status: draft
level: reference
label: FUSE and the filesystem interface
---

# The filesystem as an agent's interface

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** agents are good at reading and writing files — that is the
harness's native interaction surface. So what happens when the "files" are
actually branches, state, or a database? FUSE lets a filesystem be a
programmable interface, and several 2025–2026 projects built agent
interfaces on exactly that idea.

## The three projects

**BranchFS** — a FUSE copy-on-write filesystem where every directory is a
branch: O(1) branch creation, atomic commit-to-parent, no root needed.
Built for agentic exploration, where an agent should fork the world,
experiment, and fold back only what worked
([BranchFS](https://github.com/rewrite-the-world/branchfs)).

**AgentFS** — SQLite-backed agent state exposed as a POSIX filesystem:
the agent's memory, tasks, and tool state are files it can read and write
with ordinary tools, instead of a proprietary API
([AgentFS](https://github.com/knite51/agentfs)).

**agent-fuse** — the inverse mapping: a database or service exposed as a
filesystem so an agent's native file tools reach it without custom
integrations.

## Why the interface matters

The claim is ergonomic: an agent's most reliable capability is file I/O,
so the most composable interface for agent state is a filesystem. BranchFS
adds the workflow primitive — copy-on-write exploration — that makes the
filesystem a *safe* exploration surface, not just a convenient one. This
connects to the runtime stage's checkpointing: a branch is a checkpoint
with a name.

## What this does not say

It does not claim FUSE replaces sandboxing, memory stores, or databases —
it is an interface layer over them. The execution-environment stage's job
is to map where each layer's boundary sits; this chapter maps one
increasingly popular boundary shape.
