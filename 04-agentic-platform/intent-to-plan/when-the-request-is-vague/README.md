---
status: draft
level: reference
label: When the request is vague
---

# One ambiguous ticket, priced

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** the stage claims vague tickets produce vague output and
review cycles that cost more than the automation saved. What is the
mechanism, and how do production flows force intent into a checkable
form?

## The mechanism

Spec-in/PR-out amplifies whatever is in the spec: a vague ticket produces
vague agent output, which produces more review cycles — the review cost
can exceed the time the automation saved
([code-agent-stack analysis](https://www.joinnextdev.com/blog/openais-code-agent-stack-changes-the-buy-vs-build-calculus)).
Ticket quality is a direct productivity input, which is why spec
discipline became an AI productivity investment.

## The forcing functions

**Codex plan mode** — grounds the request in facts first: "eliminate
unknowns in the prompt by discovering facts, not by asking the user", and
emits a plan-only output with exact file paths and structures
([plan mode](https://github.com/openai/codex/pull/10195)).

**Jules** — clones the repository, drafts a plan for approval, then
returns a diff.

**Spec Kit** — the 8-phase pipeline that makes a spec the first artifact
([GitHub Spec Kit](https://github.com/github/spec-kit)).

## What this means for this topic

The mission's a-minimal-planner demo is the forcing function at mechanism
scale: it refuses to invent file paths, which is the same move plan mode
makes. Vague intent cannot survive a planner that requires exactness.

## What this does not say

It does not claim every ticket can be fully grounded upfront — some
ambiguity is discovered during execution. It claims the forcing functions
move the discovery earlier, where it is cheaper.
