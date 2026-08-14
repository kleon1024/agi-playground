---
status: draft
level: reference
label: Codebase retrieval
---

# The agent's view of a large repository

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** the largest failure mode in large-project agent work is not
reasoning — it is retrieval. An agent whose search is limited to the
current directory cannot see the rest of the tree. What does the industry
build to give agents a real view of a repository?

## The problem, measured

Sourcegraph's 2026 guide names "monorepo blind spots — searches limited to
the current working directory miss the rest of the tree" as a dominant
failure, and built CodeScaleBench (370+ software-engineering tasks, 9
languages) to measure retrieval quality on large-codebase work
([Agentic coding in 2026](https://sourcegraph.com/blog/agentic-coding)).
A 90-file monorepo refactor case showed baseline agents failing on 216
cross-package imports — a retrieval failure, not a reasoning one
([Bito case](https://bito.ai/blog/the-90-file-monorepo-refactoring-that-coding-agents-failed-and-ai-architect-nailed)).

## The mechanisms

**Repo maps** (Aider) — a compact symbol summary of the tree.

**AST and symbol indexes** (Cursor, Continue) — symbol-level search with
definition/usage graphs.

**Code intelligence graphs** (Sourcegraph) — cross-repo references,
backlinks, and type information, the deepest view.

## Why it belongs in the memory stage

Codebase retrieval is memory for code: the agent's knowledge of the
repository it works in, retrieved on demand instead of crammed into
context. It is the "when retrieval belongs" chapter's canonical yes-case.
The mission's tasks are single-file-scale; this is the scale where
retrieval decides success.

## What this does not say

It does not claim any index is sufficient — retrieval quality must be
measured per codebase (CodeScaleBench exists for that). It maps the
mechanisms and the failure they exist to close.
