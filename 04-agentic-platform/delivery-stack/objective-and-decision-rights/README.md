---
status: draft
level: frontier
base: none
label: Objective and decision rights
---

# Two requests can share every task and still need different decisions. What does the objective have to carry?

**Question:** [the intent stage](../) showed that a request is a constraint
set, and that "why" must survive as the replanning function. This chapter
takes the next step: two requests can share the same local tasks and still
demand different decisions. "Improve conversion without sacrificing
long-term retention" and "ship fastest, accept technical debt" produce
overlapping work and opposite choices when a constraint conflicts. What
does the objective have to carry for those choices to be the requester's
and not the agent's guess?

**The artifact this chapter follows** is this mission's own
[`mission.yaml`](../../mission.yaml) read as an objective contract — the
only complete one in this repository, and the proof that the fields below
are not theoretical.

**Before this:** the intent stage's constraint-set model and the corrected
"why survives" claim. This chapter formalizes what "why" has to be.

## An objective is not a constraint set

The constraint set answers *what must hold*. It does not answer *what to
do when two constraints cannot both hold* — and that is the decision every
real objective eventually forces. The mission's `mission.yaml` carries the
answer as a pair of explicit fields:

| The mission's field | What it decides |
|---|---|
| `primary_metric` | resolve rate AND cost per resolved task — a pair, because a single number would let one arm win by gaming the other |
| `baseline` | what the result must beat — no harness, always-frontier |
| `guardrails` | what may not happen even if the metric is met — the test-tampering diff check |
| `budgets` | what the run may cost before it stops — the declared spend ceiling |
| `acceptance` | what counts as done, checkable per bullet |
| `proves` / `does_not_prove` | what the evidence is and is not |

The `primary_metric` row is the sharpest: "resolve rate" alone would make
the always-frontier arm look best; "cost per resolved" alone would make
the cheapest arm look best; the pair forces the trade-off to stay visible.
That is what an objective does that a constraint set cannot — it names the
trade-off before the conflict happens.

## The objective contract

Generalize the mission's fields and you get the shape every delivery
objective needs, with each field answering one question:

| Field | The question it answers |
|---|---|
| desired outcome | what changes in the world, in observable terms |
| utility / priority | how are outcomes ranked when they conflict |
| constraints | what must hold regardless |
| non-goals | what this work explicitly is not doing |
| budget | what it may cost, in money and time |
| deadline | when it must land |
| risk tolerance | how much failure is acceptable |
| decision owner | who answers the questions above when they change |
| acceptance evidence | what proves done, and who checks it |
| rollback policy | what happens if done turns out wrong |
| known unknowns | what is not yet knowable, and when it gets resolved |
| human decisions | which calls may never be delegated |

Twelve fields, but the load-bearing ones are three: **utility** (how
conflicts resolve), **decision owner** (who resolves them), and
**acceptance evidence** (what "done" means). The other nine are
scaffolding around those three.

## Four kinds of unknown, and who owns each

The intent stage drew the boundary for grounding: descriptive unknowns
live in the repository and can be discovered. The objective contract makes
the other three explicit, because each has a different owner:

| Unknown | Example | Who resolves it |
|---|---|---|
| Descriptive | where is the file, what does the interface do | the agent, by grounding |
| Normative | speed over reliability, which customers may be affected | the decision owner |
| Predictive | what a three-month delay costs | analysis or experiment, then the owner |
| Authorization | may this be auto-merged, may this deploy | explicit approval, never the agent |

An objective contract that fails to name its normative, predictive, and
authorization unknowns does not make them disappear — it makes the agent
guess them. That is the difference between a request and a contract: the
request compresses all four kinds into one sentence; the contract assigns
each to the layer that can actually resolve it.

## Decision rights: why owner is not a label

The `decision owner` field is not metadata; it is the guard against the
delivery system's common-mode failure. If the system that proposes work
also decides what the objective means, approves the plan, and judges the
result, then a wrong objective is never caught — every downstream layer
inherits it. The mission's structure shows the separation in miniature:
the mining rule decides what a task is, the harness executes, the test
scores, and [the report](../../report/) refuses to soften the verdict.
Four roles, four owners. An objective whose owner is the same system that
executes it has no independent check on itself.

## What this does not say

It does not claim an objective contract removes ambiguity — it moves the
ambiguity to the owner, which is where it can be resolved instead of
guessed. It does not claim the mission's `mission.yaml` is a production
objective; it is an objective for a benchmark, and the chapter says so.
And it does not claim twelve fields is the right number — the number is
incidental; the three load-bearing fields are the point.

**Next:** an objective names what to achieve. The next object names what
the world actually is — the domain model and system of record.
