---
status: draft
level: frontier
label: The authorization matrix
---

# Autonomy is granted per task type, not per tool

**Question:** the mission's routing decision already grants per-task
autonomy — cheap, frontier, or decline. The industry's 2026 version of that
decision is an authorization matrix: each task type gets an autonomy level
and a gate, tuned on measured operating parameters. What does the matrix
look like, and how do you know your own is too permissive?

**The artifact this chapter follows** is the mission's own routing policy
written as that matrix — the same recorded arms, read as an authorization
decision instead of a cost decision.

By the end you will be able to write an authorization matrix for any
production harness, name its risk signals, and state the operating
parameters that tell you when to tighten or loosen it.

## The shape of the matrix

The 2026 consensus ([Tembo's autonomy guide,
2026-07](https://www.tembo.io/blog/autonomous-coding-agents); Swarmia's
five-level model) grants autonomy by task type, with three control
properties that do not depend on the model:

| Task type | Autonomy | Gate |
|---|---|---|
| dependency bumps, formatting, docs | high | review the PR |
| test generation, scoped bug fixes | high, failing test first | review the PR |
| feature work in well-covered code | medium | human review before merge |
| auth, payments, migrations, infra | low | explicit approval before any edit |

The three control properties are **reversibility** (small, rollback-able
diffs), **approval gates** (propose, then approve before merge), and a
**review artifact** (a PR with a diff and passing tests — never a direct
push to main).

## The mission's routing, read as the matrix

The mission's `cheap-or-expensive` stage measured a routing decision: the
cheap tier resolved 6/6 but hid latent defects the metric cannot see; the
frontier tier cost \$0.82 per resolved. Read as an authorization matrix,
that is a policy row for "scoped bug fix in a well-covered repo": high
autonomy on the resolve signal, but a patch-generality gate that the cheap
tier fails — the matrix equivalent of "review the PR, and the reviewer
knows to read the diff".

The measured tuning parameters are the same ones Cursor reports using
([Arize Observe 2026](https://arize.com/blog/inside-cursors-agent-factory-how-it-verifies-ai-written-code/)):
escaped defects, rollback frequency, and human overrides. Cursor's own
ecosystem merges roughly 30–40% of PRs without human review — on
risk-scored, evidence-complete changes. The threshold is an operating
parameter, not a constant: loosen it when escapes stay flat, tighten it
when they rise.

## What this does not say

It does not say high autonomy is wrong. It says autonomy is a property of
the control setup — the 2026 answer is "as autonomous as your control setup
safely allows, and no more" — and that the ceiling is set by reversibility,
gates, and review artifacts, not by model capability.

**Next:** [autonomy levels](../) — the spectrum the matrix dials along, and
where production value concentrates.
