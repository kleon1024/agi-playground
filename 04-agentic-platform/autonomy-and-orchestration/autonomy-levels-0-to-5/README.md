---
status: draft
level: reference
label: Autonomy levels 0 to 5
---

# The autonomy spectrum, and where production value concentrates

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** "autonomy" is a spectrum, not a dial. The industry's
reference model (Swarmia's five levels, echoed by Tembo and Anthropic)
runs from assistive to agentic avalanche. Where does real production value
concentrate, and why is the top of the spectrum a trap?

## The levels

| Level | Name | What it does | What you provide |
|---|---|---|---|
| 1 | Assistive | inline suggestions, refactors in one file | all context, manually |
| 2 | Conversational | chat that navigates the repo and runs tools | direction plus a good AGENTS.md |
| 3 | Task agent | hand off a task, come back to a PR | the task and the review |
| 4 | Autonomous teammate | picks work from a backlog, like Dependabot | a backlog and guardrails |
| 5 | Agentic avalanche | orchestrators spawning subagents under minimal oversight | orchestration, most teams do not need it |

Source: [Tembo's autonomy guide](https://www.tembo.io/blog/autonomous-coding-agents),
based on Swarmia's model.

## Where the value is

Level 3 is where most real productivity lives in 2026: handing off a scoped
task and reviewing a PR are workflows engineers already trust. The trap is
treating Level 5 as the destination — more agents with less oversight
multiply both output and the cost of a bad decision. Anthropic's
~400K-session empirics ground the same curve: the ceiling is set by your
control setup, not the model.

## What this means for this topic

The mission's routing decision sits between levels 2 and 4: a scoped task
with a review gate is level 3; the cheap-tier auto-resolution on 6/6 is a
level-4 experiment whose latent defects the patch-generality check caught.
The authorization-matrix chapter is how the dial gets set per task type.

## What this does not say

It does not claim higher is worse — it claims the right level is the
highest at which you can still review the result before it reaches users.
The spectrum is a decision surface, not a score.
