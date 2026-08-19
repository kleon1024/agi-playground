---
status: draft
level: frontier
base: none
label: Bounded improvement
---

# The system proposes changing itself. Who evaluates, and who deploys?

**Question:** [closing-the-loop](../../closing-the-loop/) showed the
smallest form of feedback: a model sees its own failure and tries again.
The market calls everything past that "self-improving," but the technical
meaning differs by an order of magnitude between a retry and a system
that rewrites its own code. This chapter draws the line: what can a
delivery system improve about itself, and — the load-bearing question —
who controls the evaluation and the deployment of that improvement?

**The artifact this chapter follows** is the improvement hierarchy: five
levels of "self-improvement," each changing something different, with the
mission's own finding and a documented industrial case placed on it.

**Before this:** [closing-the-loop](../../closing-the-loop/) and the
delivery-stack objects that a self-improving system would touch — the
RunLedger it learns from and the PolicyDecision it must not override.

## Five levels, only two of which are learning

The market collapses five different mechanisms into one word
([the audit's own taxonomy](https://arxiv.org/abs/2505.22954)):

| Level | What changes | Is it learning? |
|---|---|---|
| Retry / reflection | the current answer, plan, or patch | no — state dies with the run |
| Memory, routing, skills | context, prompts, or routes for next runs | stateful adaptation — the model itself is unchanged |
| Harness evolution | the agent's own code, tools, workflow | controlled program search |
| Post-training | model parameters, via RL or fine-tuning | the model actually changes |
| Open-ended RSI | the system's architecture, evaluator, and goals | not yet demonstrated |

The mission's closing-the-loop finding sits on level 1: feeding the model
its real failure moved resolve from 0/12 to 2/12, and the page says
explicitly — no parameter update, no cross-task accumulation, no
continuous learning. It is execution-feedback retry, and calling it RSI
would be the same inflation the market commits.

## What controlled program search actually looks like

The credible industrial case sits on level 3. Sakana AI's Darwin Gödel
Machine ([arXiv:2505.22954](https://arxiv.org/abs/2505.22954), ICLR 2026)
maintains a lineage of agent variants, lets variants rewrite their own
code, and selects descendants by a fixed evaluator: SWE-bench improved
from 20.0% to 50.0% and Polyglot from 14.2% to 30.7%, with the
SWE-evolved agent also reaching 28.9% on Polyglot, a benchmark never
touched during search.

Read that result with the delivery stack's vocabulary and the structure is
unmistakable: **candidate generation, sandboxed execution, an evaluator
that is not the candidate, selection, mutation, repeat.** The system
improves itself within a fixed environment, against a fixed evaluator,
inside a human deployment boundary. What it does not do is choose its own
goal, change its evaluator, or deploy itself. That is the line between
bounded and open-ended improvement, and it is not a line the industry has
crossed.

## The failure of unboundedness: Goodhart and common-mode

Two failures define why the line must be drawn. The first is Goodhart's
law, which this repository has already met at small scale: the mission's
own [origin story](../../README.md) — a serving engine that got *faster*
by attending to one token — is a metric being optimized instead of a
result. The second is common-mode failure: if the system that proposes an
improvement also controls how it is evaluated, whether it passes, and
whether it deploys, then a wrong improvement is never caught, because
every downstream layer shares its error.

## The credible bounded loop

A delivery system may therefore propose changes to itself, and nothing
more. The proposal pipeline is the trust boundary's strongest layer
applied to the system itself:

```text
proposal -> offline eval -> held-out set -> adversarial set
         -> security review -> approval -> canary -> monitor -> rollback
```

Each stage is owned by a different object: the proposal comes from the
agent, the held-out and adversarial sets come from the EvidenceRecord's
"what the run does not prove" boundary, the approval comes from the
PolicyDecision object, and the canary and rollback come from the
side-effect semantics' compensation. The invariant that makes the loop
credible is negative: **the proposer cannot control evaluation,
deployment authority, or rollback.** Those live outside its reach, which
is the same separation the mission's guardrail demonstrates at one-task
scale — the diff check is not performed by the model.

## What this does not say

It does not claim bounded improvement is easy — the proposal pipeline is
as hard as the delivery stack itself, which is why every stage above is
draft. It does not claim open-ended RSI is impossible; it claims it is
undemonstrated and that the difference matters. And it does not claim the
mission can implement any of this — it has one finding on level 1 and the
honest statement that the other levels are the agenda, not the result.

**Next:** the six objects are mapped. What would it take to run them as
one system on a real delivery — the two capstones.
