---
status: draft
level: frontier
label: Spec-driven development
---

# The three moves, institutionalized

**Question:** the stage's three moves — ground, write exactly, gate — are
what any single harness needs. Spec-driven development is what happens
when a team institutionalizes them: the spec becomes the first artifact,
the review becomes the gate, and the pipeline makes the moves routine
across an organization. What does the institutional form actually
contain, and why did it win?

**The artifact this chapter follows** is the 8-phase pipeline of GitHub
Spec Kit — the reference implementation of spec-driven development, open
source since 2026 and compatible with 30+ coding agents
([Spec Kit](https://github.com/github/spec-kit);
[DevOps.com](https://devops.com/githubs-spec-kit-puts-the-spec-back-in-software-development/)).

## The pipeline, read as the three moves

Spec Kit's phases are usually listed as a sequence; they are better read
as the three moves with the failure taxonomy attached:

| Phase | The move it enforces | The ambiguity row it closes |
|---|---|---|
| constitution | ground in the repo's standards | implicit constraints (row 2) |
| context | ground in the codebase and prior work | unresolved referents (row 4) |
| spec | write the constraint set as the first artifact | missing acceptance criteria (row 1) |
| plan | make the spec executable | level confusion (row 3) |
| execute | agent fills the cells | — |
| verify | tests against the spec's criteria | contradiction (row 5) |
| review | the gate, at spec speed | every row, one more time |
| merge | the signed result | — |

The constitution phase is the part teams new to spec-driven development
miss, and it is the most important: it moves the repo's implicit
constraints (style, architecture, "don't break X") out of the reviewer's
head and into a written document the agent reads first. That is row 2 of
the taxonomy — the only row grounding can partially close by writing the
constraint down before the request exists.

## Why the spec is not the point

The point is not that a spec document exists — it is that the spec moves
the loss chain's leak points *before* the expensive surfaces. A spec
reviewed before execution converts the ticket→plan loss (row 1–4) from
something discovered on a diff into something resolved on a document. The
industry's measured framing is direct: ticket quality is a productivity
input, and vague tickets produce review cycles that cost more than the
automation saved
([code-agent-stack analysis](https://www.joinnextdev.com/blog/openais-code-agent-stack-changes-the-buy-vs-build-calculus)).

## What this means for this topic

The mission's a-minimal-planner demo is the spec pipeline at mechanism
scale: the task record is the mined spec, the plan is the executable
projection, and the harness's scorer is the verify phase. A team adopting
spec-driven development is doing the same thing with humans where the
demo uses records.

## What this does not say

It does not claim spec discipline is free — it is a skill the industry is
hiring for, and over-specification is a real failure (a plan whose review
cost exceeds the change it governs). It claims the institutional form is
the three moves made routine, and that reading it that way is what keeps
it from collapsing into paperwork.
