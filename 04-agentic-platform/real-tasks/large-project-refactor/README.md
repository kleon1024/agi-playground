---
status: draft
level: reference
label: Large project refactor
---

# When the artifact is a codebase, not a function

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** the mission's tasks are bug fixes in small scope. Large
project refactors are a different kind — 90 files, 216 cross-package
imports, and a retrieval problem that decides success before any code is
written. What changes, and what does an agent need to survive it?

## The failure mode

Baseline coding agents fail on monorepo-scale refactors because they
cannot see the tree: searches limited to the working directory miss the
rest of the repository. The Bito case — restructuring 90 TypeScript files
and updating 216 cross-package imports — failed for baseline agents and
succeeded with an architect agent that planned the change before
executing ([case study](https://bito.ai/blog/the-90-file-monorepo-refactoring-that-coding-agents-failed-and-ai-architect-nailed)).
Sourcegraph's CodeScaleBench (370+ tasks, 9 languages) exists to measure
this retrieval quality directly
([guide](https://sourcegraph.com/blog/agentic-coding)).

## What survives the scale change

The intent-to-plan stage becomes non-optional: a refactor without a
plan-as-contract is a refactor that guesses. Codebase retrieval (stage 9)
becomes the deciding capability. The authorization matrix tightens — a
refactor touches everything, so reversibility and review gates are not
optional.

## What this means for this topic

The mission's platform stages are the answer set: plan (intent), retrieve
(codebase), execute (harness), verify (gates), review (matrix). This
chapter maps where the mechanism-scale demos sit in a scale that needs
all of them.

## What this does not say

It does not claim this topic reproduces monorepo refactors on the local
lane — the case studies are dated surveys. It maps what the platform must
have at that scale.
