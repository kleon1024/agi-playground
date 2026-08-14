---
status: draft
level: reference
label: The human-in-the-loop economy
---

# What human time is actually for now

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** if the agent writes the code, what do the engineers do? The
industry answer is a role shift, not a layoff: humans write specs, design
gates, and review evidence — and the org gets smaller and more senior.
What is the new division of labor, and how do you measure it?

## The new roles

OpenAI's own stack analysis frames it as the "Navy SEAL model": architects
who write tight specs, leads who design approval gates and CI, reviewers
who evaluate agent output quickly
([code-agent-stack analysis](https://www.joinnextdev.com/blog/openais-code-agent-stack-changes-the-buy-vs-build-calculus)).
The human is not typing code; they are reviewing decisions and approving
outputs.

## The economics

The gate costs seconds when the agent is right and saves an incident when
it is wrong — the approval gate is the cheapest insurance in the stack.
The measurable outputs are review load, escaped defects, and rollback
frequency; Cursor runs its 30–40% unreviewed-merge rate against exactly
those parameters ([Arize write-up](https://arize.com/blog/inside-cursors-agent-factory-how-it-verifies-ai-written-code/)).
DORA's finding — AI increases throughput while exposing instability
downstream — is the reason the review load is a first-class metric.

## What this means for this topic

The mission's routing decision is this economy at mechanism scale: the
maintainer's time is the scarce resource, and the resolve-rate/cost pair
is how a gate is priced. The authorization matrix is the written form of
the economy.

## What this does not say

It does not claim the role shift is painless — spec-writing and
fast-review are skills the market is still learning to hire. It maps the
new division of labor and its metrics.
