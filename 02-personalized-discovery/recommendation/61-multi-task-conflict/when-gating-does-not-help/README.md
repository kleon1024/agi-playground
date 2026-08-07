---
status: verified
level: applied
base: scratch
label: When gating does not help
verified: 2026-08-07
---

# One expert, two copies of the same trunk

**Question:** [stage 61](../) shows gating improving on a naive shared
bottom. This chapter asks when gating is the wrong answer, and answers:
when both tasks want the same representation, the gate collapses to a
single expert and the architecture is a shared bottom with extra
parameters.

**Before this:** [stage 61 — multi-task conflict](../).

## The collapsed gate, executed

The run ([record](runs/2026-08-07-gating-no-help.md)) reads the learned
gate weights:

| task | expert0 | expert1 |
|---|---:|---:|
| task 0 | 0.99 | 0.01 |
| task 1 | 0.98 | 0.02 |

Effective architecture: one expert, two copies of the same trunk.

## The reading

MMoE pays off when tasks disagree about which expertise they need —
different features, different regimes. When both tasks want the same
representation, the gate collapses to a single expert and the architecture
is a shared bottom with extra parameters and more serving cost. The
diagnostic is to look at the learned gate weights and the per-task gain
over a plain shared bottom before committing to gating: if the gates are
all one-hot on the same expert, the complexity is not earning its keep.

## Evidence boundary

The executed read over a task pair declared to agree (illustrative,
deterministic). It demonstrates the collapse; real systems must audit the
gate weights per slice and compare per-task gains against a shared bottom
baseline.

## Check your mental model

Answer each before opening it.

**1. What does a collapsed gate mean structurally?**

<details>
<summary>Answer</summary>

That the routing decision is not doing anything: every task picks the same
expert, so the model has one effective representation and the extra
experts are dead weight.

</details>

**2. What is the cheapest way to avoid paying for a collapsed gate?**

<details>
<summary>Answer</summary>

Train a shared bottom first, then check whether gating beats it per task
before shipping the bigger architecture; and log the gate weights so a
later collapse is visible.

</details>

## Next

Back to [stage 61](../). The imbalance that gating is meant to fix: [the
dominant task owns 98.9% of the trunk gradient](../when-the-dominant-task-wins/).
