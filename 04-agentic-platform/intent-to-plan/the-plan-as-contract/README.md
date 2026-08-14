---
status: draft
level: frontier
label: The plan as contract
---

# The plan is the intent's verifiable projection

**Question:** a plan is not a summary of the request — it is a projection:
the constraint set, mapped onto a form the agent can execute and a human
can check. Projection is a lossy operation, and the whole design question
is *what a plan may lose*. What must a plan keep, what may it drop, and
why is "plan-only" a property rather than a style?

**The artifact this chapter follows** is the projection rule, read off the
mission's real plan artifact and the industry's plan-mode outputs.

## The projection rule

A projection from intent to plan must preserve exactly three things and
may drop everything else:

| Must preserve | Why | Where it lands |
|---|---|---|
| acceptance criteria | without it, "done" is unfalsifiable | target tests |
| scope | without it, the agent may fix the wrong thing | exact file paths |
| verification | without it, nobody can check the result | test command |

| May drop | Why | What absorbs it |
|---|---|---|
| the reason | it changes nothing the tests check | the spec/context, if anywhere |
| the solution design | it is the agent's decision, not the requester's | the execution itself |
| the ground truth | it would make the plan claim the result | the task record |

The mission's plan artifact is this rule in concrete form:

```text
# Plan: attend past the first token in every cached decode step

## Files to change
- `missions/01-language-model-agent/05-serve/core/engine.py`

## Tests this must satisfy
- `tests/test_decode_correctness.py`

## Verification
uv run --group torch pytest -q tests/test_decode_correctness.py

## What the plan does not claim
- It does not claim the fix; the test decides that.
- It does not claim the ground truth: that stays in the task record.
```

The last section is the projection's honesty clause: it names what the
plan drops, so a later failure can be attributed to the plan instead of
to bad luck. A plan that claims the fix has collapsed the projection into
the result, and the test's verdict loses its meaning.

## Why plan-only is a property, not a style

Codex's plan mode requires the final plan to be *plan-only* — a title, a
TL;DR, exact paths and structures, nothing else
([plan-mode change](https://github.com/openai/codex/pull/10195)). The
requirement is not tidiness; it is a guarantee about the projection. A
plan that also contains the reasoning, alternatives, or the expected
result cannot be reviewed at plan speed — the human has to separate the
claims from the decisions, which is exactly the work the gate is supposed
to be cheap. Plan-only is what keeps the gate at its measured cost:
seconds when the agent is right, an incident averted when it is wrong.

## The TL;DR checkpoint

The TL;DR in a plan-only output is the projection's index: three to five
bullets a reviewer can read before deciding whether to open the details.
It exists because the gate's economics depend on the reviewer's *first
decision* (read further or reject) being near-free. A plan whose first
three lines do not let a human decide whether to engage is a plan whose
gate will be skipped — and a skipped gate is the loss-control point the
previous chapter priced as the most expensive leak.

## What this does not say

It does not claim every task needs a heavyweight plan — the projection's
cost must be proportional to the change, and trivial changes should skip
the gate. It establishes the projection rule and why the gate depends on
it.
