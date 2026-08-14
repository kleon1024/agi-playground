---
status: draft
level: frontier
label: Context and memory
---

# What does the agent remember, and how does it get what it forgot?

**Question:** the mission's closing-the-loop stage showed that feeding a
model the real outcome of its own failure changes the next attempt. That is
memory in its smallest form. Production agents need three more: a
repository's instructions that survive every session, a record of prior
sessions the agent wrote itself, and retrieval (RAG in its modern form) for
knowledge that never fits the context window. How do the tiers fit
together, and what does each one forget?

**The artifact this stage follows** is a memory map: the instruction layer,
the generated-summary layer, and the retrieval layer, drawn over the
mission's own closing-the-loop run so every tier has a real anchor.

By the end you will be able to read any production memory setup (Claude
Code's CLAUDE.md scopes + auto memory, Codex's AGENTS.md + rolling
summaries, a Mem0/Letta/Zep stack) as the same tiers, and say which tier a
given failure — stale instruction, forgotten session, wrong retrieval — came
from.

**Before this:** [stage 06](../closing-the-loop/) showed one-loop feedback.
This stage scales that loop across sessions and codebases.

## What this stage decides

What is allowed to influence the agent's next run. Memory is not free:
every instruction competes for context, every auto-summary can be stale,
every retrieval can miss. The decision is which tier owns which fact, and
when a fact is promoted, demoted, or deleted.

## Planned chapters

- **from-rag-to-agentic-rag** — how retrieval evolved from corpus search to
  a tool an agent calls mid-task; when RAG belongs in an agent and when it
  is the wrong layer (industry: hybrid retrieval moving buyer-intent
  signals, and the "RAG is not memory" distinction).
- **file-based-memory** — the two-layer file system memory that dominates
  coding agents: the static instruction layer (AGENTS.md / CLAUDE.md, now a
  Linux Foundation standard across 20+ tools) and the generated layer
  (Codex rolling summaries, Claude auto memory), plus memory hygiene —
  promotion rules, audits, and the cost of an unpruned instruction file.
- **memory-tiers** — working / episodic / semantic memory and the
  production stack (SQLite-first local, vector for retrieval, graph when
  entity relationships matter); the measured costs of selective memory
  (Mem0's paper: ~90% token reduction).
- **codebase-retrieval** — the agent's view of a large repository: repo
  maps, AST and symbol indexes, code intelligence graphs (Sourcegraph),
  and why "monorepo blind spots" are the dominant failure in large-project
  agent work.
- **a-sqlite-memory** (local mechanism demo) — a minimal SQLite memory
  store + retrieval on top of the mission's recorded runs, showing a
  promoted lesson changing a later attempt.
- **agentfs-and-persistent-workspace** — filesystem-backed agent state
  beyond the context window: AgentFS, BranchFS workspaces, and the
  persistent-session pattern.

## Evidence strategy

`a-sqlite-memory` runs locally against the mission's recorded JSONL. The
rest are dated surveys; the Mem0 token-reduction figure and the
observational-memory benchmark results are attributed to their papers.

## Industrial grounding

Codex separates AGENTS.md (static instructions) from Memories
(auto-generated session summaries); Claude Code reads four CLAUDE.md scopes
at session start and auto-captures learnings. Mem0's paper reports
selective fact-based memory cutting token cost by over 90% and p95 latency
by 91% versus full-history prompting. Sourcegraph's 2026 guide names
monorepo blind spots — searches limited to the current directory — as the
dominant large-codebase failure.
