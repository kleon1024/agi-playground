---
status: draft
level: frontier
label: When the request is vague
---

# The ambiguity taxonomy: five ways a request can be missing constraints

**Question:** "vague" is not one thing. A request can be missing its
acceptance criteria, its implicit constraints, its level, its referents,
or it can be internally contradictory — and each failure has a different
signal and a different fix. What is the taxonomy, and how does each
production flow close the specific gap?

**The artifact this chapter follows** is the taxonomy itself, with each
row tied to a real request shape and the move that closes it.

## The five failure modes

**1. Missing acceptance criteria — "make it faster".**

The intent has no verifiable "done". *"The search box is slow"* contains a
perception, not a constraint; *"search must return top-100 results under
200ms, measured on the recorded query set"* contains one. This is the most
common failure and the one a failing test closes by construction — the
mission's tasks skip this failure entirely because the miner only admits
tasks whose test fails at base and passes at gold.

Signal: no number, no comparison, no test in the request.
Fix: grounding discovers what the request *could* be verified against;
the plan names the test that will decide done.

**2. Missing implicit constraints — "don't break the filters".**

The most expensive category, because it is invisible: the constraint the
requester holds but never states. The mission's own artifact shows it —
the record carries `source_files` and `target_tests`, but "nothing that
passed before must stop passing" is absent from the record and had to be
re-derived as a regression check in stage 03. No grounding move can
discover a constraint the requester did not state; only a human reviewing
the plan can supply it. This is why the approval gate is the only fix, and
why it sits *before* execution rather than after.

Signal: the request mentions what should not change ("keep X working",
"without breaking Y").
Fix: the gate, plus a regression baseline the agent is scored against.

**3. Execution intent standing in for task intent — "add caching".**

The request states a solution, not the problem. *"Add caching to the
search"* is execution intent; the task intent is *"search is slow"*, and
the constraint set (query set, latency budget, correctness requirements)
is what makes it verifiable. An agent that executes the solution cannot
verify the task: a cache can be added and the search can stay slow.

Signal: the request contains a verb of implementation (add, refactor,
migrate, introduce) and no acceptance language.
Fix: ground the solution back to the problem — what does the solution
claim to fix, and how would we know it did?

**4. Unresolved referents — "fix the bug I mentioned".**

The request points at context that is not in the request: a previous
conversation, a ticket number, a commit, an unstated assumption about
which search box. Codex's grounding rule is the explicit answer: discover
the referent from the repository rather than re-negotiating it. Jules
mechanizes the same move by cloning and inspecting before planning.

Signal: pronouns and pointers ("that thing", "the issue", "as discussed")
with no resolvable target in the request.
Fix: grounding — resolve the referent against the repository and the
conversation, and write the resolved target into the plan.

**5. Contradiction — "keep it simple, but support every input format".**

The constraint set is internally inconsistent, and no plan can satisfy it.
Contradictions surface only when the constraints are written down side by
side, which is exactly what a plan does — the plan's exactness makes the
contradiction visible *before* execution instead of after.

Signal: two constraints that cannot both hold, detected when the plan
names both.
Fix: the gate — a human resolves the conflict; the plan records the
decision so the agent does not have to guess.

## Why the taxonomy matters

A vague request is not one problem with one fix. "Write clearer tickets"
collapses five distinct failures into one slogan; the taxonomy separates
them, and each row has a different mechanism: tests for missing criteria,
the gate for implicit constraints, grounding for referents, plan
exactness for contradictions, and the problem/solution split for level
confusion. The production flows are not interchangeable answers to
"vagueness" — each one is a specific loss-control device aimed at specific
rows of this table.

## What this does not say

It does not claim every ambiguity can be closed upfront — some constraints
only surface during execution, and the loop has to handle them then. It
claims the taxonomy is the map: naming the failure is what makes the fix
mechanism-able instead of aspirational.
