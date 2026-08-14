---
status: draft
level: frontier
label: Harness comparison
---

# Every production harness is the same five decisions. Where do they differ?

**Question:** stage 03 built one harness by hand. Claude Code, Codex,
Cursor, and the agent SDKs are marketed as different products, but if the
software around the model really is the independent variable in agent
scores, then reading a production harness should be the same exercise as
reading our own — with the five decisions (loop, tools, sandbox, context,
permission) filled in differently. Is that true, and does the difference
matter more than the model?

**The artifact this stage follows** is a comparison table: every harness
read as the same five decisions, with the recorded arms of stage 03 as the
reference column.

By the end you will be able to take any production harness — Claude Code,
Codex CLI, Cursor, pi, an agent SDK — and say which of the five decisions it
owns, which it delegates, and what that means for a score it reports.

**Before this:** [stage 03](../agent-loop/) built the reference harness and
its verified runs. This stage reads other people's harnesses against it.

## What this stage decides

Which harness to adopt or build around is a buying and architecture
decision, but the stage's real decision is deeper: where the score came
from. "Stop comparing agents without disclosing the harness" is the field's
own warning — two teams reporting different scores for the same model are
often running different harnesses. This stage makes harness disclosure a
reading skill.

## Planned chapters

- **when-the-harness-moved-the-score** — the recorded external case where
  changing harness settings alone moved a benchmark 3x (OpenAI's ARC-AGI-3
  post); moved from the old `harness-effects-landscape` reference.
- **reading-claude-code** — the terminal harness read as five decisions:
  its loop, subagents, sandbox (v2.1+, filesystem + SOCKS5 network policy),
  CLAUDE.md context scopes, and permission ladder.
- **reading-codex** — the CLI and cloud harness: plan mode, approval
  policy (untrusted / on-request / never), sandbox layers (process
  isolation, network policy, approval routing), AGENTS.md + rolling memory.
- **reading-cursor-and-open-source-harnesses** — editor-first agents,
  background agents, and the open harnesses (OpenHands, SWE-agent) as the
  same five decisions with different defaults.
- **pi-and-the-agent-sdks** — the composition layer: pi's unified API and
  agent loop, OpenAI Agents SDK's built-in Runner, guardrails, handoffs,
  and subagents, Claude Agent SDK's query/receive-response cycle.

## Evidence strategy

All chapters are dated surveys or reads of published docs; the one number
this stage may cite from our side is the recorded harness-vs-no-harness
delta from stage 03, which is run-backed. No new runs are planned here —
the comparison is a reading exercise, not a benchmark.

## Industrial grounding

Claude Code shipped native sandboxing in v2.1.0 with a SOCKS5 network proxy
and domain allowlist. Codex documents three sandboxing layers and an
approval policy ladder. OpenAI's ARC-AGI-3 post showed harness settings
moving a score from 13.3% to 38.3% with 6x fewer tokens. SWE-bench-Live
(2025–2026) reported state-of-the-art systems at 19.25% on the live set vs
43.20% on the static Verified split — the gap this stage teaches you to
attribute to the harness, not the model.
