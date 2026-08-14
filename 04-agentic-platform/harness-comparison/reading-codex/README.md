---
status: draft
level: reference
label: Reading Codex
---

# The CLI and cloud harness, read as five decisions

> Dated survey, 2026-08-14. Sources: official Codex documentation
> (developers.openai.com/codex), read but not re-measured here.

**Question:** Codex is the other dominant production harness, and it
fills the same five decisions differently from Claude Code — most visibly
in planning and approval. What are its five answers?

## The five decisions

**Loop.** The CLI runs the tool loop locally; the cloud service clones the
repository into an isolated sandbox, works on a branch, and proposes a
PR — the spec-in/PR-out pattern the orchestration stage documents as the
industry's organizational redesign.

**Tools.** Bash, file edits, and MCP servers, with a plan mode that forces
grounding — "eliminate unknowns in the prompt by discovering facts, not
by asking the user" ([plan mode PR, OpenAI/codex](https://github.com/openai/codex/pull/10195)).

**Sandbox.** Three documented layers: process isolation, network policy,
and approval routing ([sandboxing docs](https://developers.openai.com/codex/concepts/sandboxing)).
`approval_policy` runs from `untrusted` (known-safe reads only) to
`on-request` to `never`.

**Context.** AGENTS.md (the static instruction layer, now a Linux
Foundation standard) plus Memories — auto-generated session summaries the
CLI writes between runs (the generated layer).

**Permission.** The approval ladder is the sandbox's third layer, not a
separate prompt instruction — policy is enforced at the boundary, which
is the control-plane lesson the governance stage develops.

## Why the plan mode matters for this topic

Codex's plan mode is the most explicit production instance of the
intent-to-plan stage's claim: a plan-only output (title, TL;DR, exact file
paths, exact structures) gated behind human approval before any edit.
The mission's a-minimal-planner demo makes the same move mechanically.

## What this does not say

It does not claim Codex's defaults are optimal — approval policy is a
per-team operating parameter, and the mission's routing runs show the
cost of each posture. It maps the harness; the pricing is elsewhere.
