---
status: draft
level: reference
label: When to orchestrate
---

# The decision rule: deterministic skeleton, LLM cells

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** when is a task workflow-shaped, and when should an agent run
free? The industry answer has hardened into a rule. What is it, and what
are the failure cases on each side?

## The rule

Anthropic's 2026 guidance: for structured, mission-critical work,
orchestrate the steps deliberately and let the agent fill the gaps; free
agents are for exploratory tasks
([multi-agent coordination patterns](https://claude.com/blog/multi-agent-coordination-patterns)).
The mission's own evidence agrees: the harness's 18/18 came from a
deterministic loop with a scorer, not from letting the model improvise the
verification.

## The failure cases on each side

**Orchestrating what should be free** — over-engineering a fixed pipeline
for exploratory work that needs branching. The cost is rigidity.

**Letting free agents run what should be orchestrated** — the
why-multi-agent-fails chapter's record: non-terminating conversations,
command races, state hallucination. The cost is multiplied faults.

## The deciding questions

Is the goal measurable? Are the steps known in advance? Can a failing step
be verified? Three yeses → workflow with LLM cells. Any no → the agent
needs freedom, and the platform needs guardrails around it.

## What this does not say

It does not claim the boundary is fixed — it moves as models improve. It
gives the decision rule and the evidence for it.
