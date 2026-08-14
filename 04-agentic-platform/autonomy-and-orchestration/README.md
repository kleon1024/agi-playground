---
status: draft
level: frontier
label: Autonomy and orchestration
---

# How much human is left in the loop, and where exactly?

**Question:** the mission's routing decision (stage 05) already grants
autonomy per task. The industry answer in 2026 is a matrix, not a dial: a
task's allowed autonomy depends on its type and risk, and the gate is a
reviewable artifact — a PR with a diff and passing tests — not a direct
push. What is the matrix, and how do teams measure whether their autonomy
level is too permissive or too cautious?

**The artifact this stage follows** is the authorization matrix for the
mission's own task set: which task types may auto-resolve, which need
approval, and which are declined — the same policy the mission's routing
already implements, now written as an explicit matrix with a risk signal.

By the end you will be able to write an authorization matrix for any
production harness, define its risk signals, and tune it on the measured
operating parameters — escaped defects, rollbacks, human overrides.

**Before this:** [stage 05](../cheap-or-expensive/) routed by price; this
stage routes by risk. [stage 12](../control-plane-and-governance/) supplied
the policy layer the matrix runs on.

## What this stage decides

How much decision the agent owns, per task type. The 2026 consensus: "as
autonomous as your control setup safely allows" — autonomy is a property of
the control setup, not the model, and Level 3 (hand off a scoped task,
review the PR) is where most real productivity lives.

## Planned chapters

- **autonomy-levels-0-to-5** — the autonomy spectrum from assistive to
  agentic avalanche; where production value concentrates (Level 3) and the
  Level-5 trap; the Anthropic ~400K-session empirical grounding.
- **[the-authorization-matrix](the-authorization-matrix/)** — grant autonomy by task type: dependency
  bumps and docs run free, auth/payments/migrations need explicit approval;
  the three control properties (reversibility, approval gates, review
  artifact) and the risk-scored auto-merge pattern (Cursor's 30–40%
  unreviewed merges on low-risk evidence-complete PRs).
- **when-the-agent-runs-itself** — meta-agents and self-extension: agents
  that write their own skills, orchestration scripts, or subagents; where
  self-modification stops being a demo and becomes a governance problem.
- **the-human-in-the-loop-economy** — what human time is actually for now:
  writing specs, designing gates, reviewing evidence — the "Navy SEAL
  model" of a smaller senior core, and how to measure review load as a
  first-class metric.
- **production-trace-evals** — the control loop that tunes the matrix:
  offline eval, CI gates, and production trace evaluation (OTel spans,
  gen_ai.evaluation.score); eval failure triggering diagnosis, not just
  dashboards.

## Evidence strategy

The authorization matrix chapter reuses the mission's recorded routing
data; the rest are dated surveys with the industry figures attributed
(Cursor's share, the autonomy-levels empirics, DORA's instability numbers).

## Industrial grounding

The 2026 consensus across Tembo, Swarmia, and Anthropic: autonomy level is a
property of the control setup, Level 3 is where production value lives, and
the gate is a reviewable artifact. Cursor reports 30–40% of its ecosystem's
PRs merge without human review on risk-scored, evidence-complete changes.
DORA's research ties AI usage to downstream instability (each 25% of AI
usage adds ~7% instability), which is exactly what an authorization matrix
exists to bound.
