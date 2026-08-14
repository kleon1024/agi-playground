---
status: draft
level: frontier
base: none
label: Autonomy and orchestration
---

# How much human is left in the loop, and where exactly?

**Question:** [stage 05](../cheap-or-expensive/) measured a routing
decision: for each task, attempt with the cheap tier, escalate to the
frontier tier, or decline. That decision is autonomy — the platform decided
how much machine was enough per task. The industry's 2026 version of the
same decision is an authorization matrix: each task type gets an autonomy
level and a gate, and the gate is a reviewable artifact — a PR with a diff
and passing tests — never a direct push. How is autonomy granted, and how
do you know your own level is too permissive?

**The artifact this stage follows** is the mission's own routing, read as
that matrix ([the-authorization-matrix](the-authorization-matrix/)): the
same recorded arms from stage 05 — cheap, frontier, decline — now read as
an authorization decision instead of a cost decision.

**Before this:** stage 05 routed by price. This stage routes by risk.
[Stage 12](../control-plane-and-governance/) supplied the policy layer the
matrix runs on.

## Autonomy is a matrix, not a dial

The 2026 consensus is explicit
([Tembo, 2026](https://www.tembo.io/blog/autonomous-coding-agents);
[autonomy-levels-0-to-5](autonomy-levels-0-to-5/)): autonomy is not one
knob from "assistive" to "autonomous". It is a per-task-type decision, and
it is a property of the *control setup*, not the model. A frontier model
with no gates is less autonomous than a weak model behind a good matrix,
because autonomy is what the setup allows to land, not what the model can
attempt.

The mission's routing is the proof of that framing. Stage 05 measured: the
cheap tier resolved 6/6 but hid latent defects the metric cannot see; the
frontier tier cost \$0.82 per resolved task. Read as an authorization
matrix, that is a policy row for "scoped bug fix in a well-covered repo":
high autonomy on the resolve signal, with a patch-generality gate the
cheap tier fails. The routing decision was never "which model"; it was
"how much of this task's outcome do we let the machine own, and what must
a human still see."

## The shape of the matrix

The matrix grants autonomy by task type, with three control properties
that do not depend on the model
([the-authorization-matrix](the-authorization-matrix/)):

| Task type | Autonomy | Gate |
|---|---|---|
| dependency bumps, formatting, docs | high | review the PR |
| test generation, scoped bug fixes | high, failing test first | review the PR |
| feature work in well-covered code | medium | human review before merge |
| auth, payments, migrations, infra | low | explicit approval before any edit |

The three control properties underneath: **reversibility** (small,
rollback-able diffs), **approval gates** (propose, then approve before
merge), and a **review artifact** (a PR with a diff and passing tests —
never a direct push). The gate is not ceremony. It is the mechanism that
lets autonomy be high where it is safe and low where it is not, without
asking the model to self-assess.

## Where the value concentrates, and the level-5 trap

Production value concentrates at Level 3 — hand off a scoped task, review
the PR ([autonomy-levels-0-to-5](autonomy-levels-0-to-5/), grounded in
Anthropic's ~400K-session operating data). Below that, the human is doing
work the agent could own; above it, the "agentic avalanche" of agents
spawning agents is where the control-plane invariants of
[stage 12](../control-plane-and-governance/) stop being exercised. Cursor's
reported 30–40% ecosystem-wide unreviewed merges
([Arize, 2026](https://arize.com/blog/inside-cursors-agent-factory-how-it-verifies-ai-written-code/))
are not evidence that review can be skipped; they are evidence that a
risk-scored, evidence-complete change can pass a tighter gate — which is
exactly what the mission's patch-generality check is, at one-task scale.

## Tuning the matrix: the control loop

An authorization matrix is an operating parameter, not a constant
([production-trace-evals](production-trace-evals/)). The measured signals
are escaped defects, rollback frequency, and human overrides: loosen the
threshold when escapes stay flat, tighten it when they rise. DORA's
research gives the stakes a number — each 25% of AI usage adds roughly 7%
instability — which is what the matrix exists to bound. And the human
time the matrix frees is not idle
([the-human-in-the-loop-economy](the-human-in-the-loop-economy/)): it
reconcentrates into writing specs, designing gates, and reviewing
evidence — a smaller senior core, with review load measured as a
first-class metric.

The frontier of the question is when the agent starts granting itself
autonomy — writing its own skills, orchestration scripts, or subagents
([when-the-agent-runs-itself](when-the-agent-runs-itself/)). That is where
"autonomy per task type" stops being a policy and becomes a governance
problem, because the agent can change the matrix from inside.

## What this stage does and does not establish

It establishes the mechanism: the matrix as the per-task-type grant of
autonomy, the three control properties, and the tuning loop, anchored to
the mission's own recorded routing read as an authorization decision. The
industry figures — Cursor's merge share, DORA's instability number, the
Level-3 concentration — are dated surveys with sources cited.

It does not claim the mission's routing *is* an authorization matrix — it
is one policy row, read as one. And it does not claim a matrix removes
risk; it claims the matrix makes risk *tunable*, which is the difference
between "the agent decides" and "the platform decides, and can be
measured."

**Next:** autonomy is set per task type. The outward question is which
industries can actually stand it — [industry impact](../industry-impact/).
