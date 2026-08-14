---
status: draft
level: reference
label: File-based memory
---

# AGENTS.md, CLAUDE.md, and the memory file that runs the repo

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** the memory map has two file layers: the static instruction
file a human writes, and the generated summaries an agent writes about
its own sessions. Both are plain markdown in the repo. Why did this
shape — not a database — win the coding-agent memory market?

## The static layer

AGENTS.md became a Linux Foundation standard read by 20+ tools (Codex,
Jules, Gemini CLI, Cursor, Copilot's coding agent, and more)
([AGENTS.md overview](https://www.tembo.io/blog/agents-md)). CLAUDE.md is
the Anthropic-side variant with four scopes read at session start.
The file is the repo's durable instruction memory: it travels with the
code, it diffs, it reviews — properties a database lacks.

## The generated layer

Codex writes rolling session summaries (Memories) in the background;
Claude Code auto-captures session learnings. The split is explicit:
AGENTS.md is what the team says, Memories are what the agent learned
([Mem0's Codex memory analysis](https://mem0.ai/blog/how-memory-works-in-codex-cli)).

## The hygiene problem

An instruction file is memory with a maintenance cost. Community
standards (memory-hygiene) enforce promotion rules — a lesson is
promoted after recurring (the two-incident rule), and the index stays
under a size budget — because an unpruned instruction file dilutes every
session. The mission's a-sqlite-memory demo implements the promotion
rule in miniature.

## What this does not say

It does not claim files replace vector memory — retrieval stores handle
open-ended recall; instruction files handle stable policy. It maps the
layer that dominates coding agents and the discipline that keeps it
healthy.
