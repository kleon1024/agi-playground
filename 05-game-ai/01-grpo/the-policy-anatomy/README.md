---
status: verified
level: applied
base: scratch
label: The policy anatomy
verified: 2026-08-06
---

# The same decoder, a reward that rewards the wrong thing

**Question:** [stage 01's GRPO run](../) trained a policy that collapsed to
constant direction strings. This chapter dissects the policy's structure
and asks what the collapse is actually a failure of.

**Before this:** [stage 01's GRPO run](../) and its recorded seeds.

## The structure, read

The run ([record](runs/2026-08-06-policy-anatomy.md)) reads the config and
the three recorded seeds:

| piece | value |
|---|---|
| architecture | mission 01's Transformer, 692,864 params |
| vocabulary | 28 characters (grid symbols + U/D/L/R) |
| reward | format credit (0.2/0.5/1.0) + terminal goal-reached bit |
| outcome | seed 0: 0.078, seed 1: 0.062, seed 2: 0.078 greedy success |

<!-- interactive: PolicyRewardAnatomy -->

## The structure, named

The policy is two parts, and only one of them is a model:

1. **The network** — mission 01's decoder, instantiated for the grid
   vocabulary, imported unmodified from `grpo.py`. The structure is a
   language model's structure: embeddings, attention, feed-forward,
   next-token head.
2. **The reward** — a two-part additive function: format credit for
   emitting legal moves (1.0 for all-legal, 0.5 for half, 0.2 for any)
   plus a terminal bit for reaching the goal.

The anatomy's finding: the *architecture is not the failure*. The same
Transformer that learns next-token prediction in mission 01 collapses here
— because the reward's format credit can be earned without reaching the
goal. A policy that emits `RRRRRRRRRRRR` gets format credit on every token
and never touches the terminal bit; group-relative advantage stays zero
when every rollout in the group fails, so no gradient step ever pulls it
out. The collapse is the reward's shape meeting a cold start, not the
network's structure.

## Comparison: the same network, a different objective

Mission 01's pretraining trains the identical block on next-token
likelihood; mission 06 trains it on the two-part reward. The parameter
count, the attention, the vocabulary plumbing are the same; the objective
is what changed — and the recorded outcome (0.062-0.078, below the random
floor of 0.222) is what the changed objective produced. That comparison is
why the mission's null result is honest: it isolates the reward as the
variable, because the architecture is a controlled constant.

## The fix and its trade

The fix this chapter installs is the controlled-variable frame itself:
hold the architecture constant (mission 01's Transformer, imported
unmodified) and change only the objective, so the collapse can be
attributed to the reward's shape rather than to the network. The trade is
that a controlled constant is also an unexamined one — the reading proves
the reward is the variable *in this comparison*, not that the
architecture is irrelevant at other scales (a larger model or a
pretrained start could change the balance, and the boundary says so). The
anatomy's verdict — format credit earnable without the outcome, plus a
cold start with zero reward variance — is what lets the fix be aimed at
the reward rather than at the model, which is the actionable outcome.

## Who owns this loop

- **The reward owner** owns the two-part objective, the named suspect:
  the format credit that can be earned without reaching the goal is the
  mechanism the reading identifies, and any fix to the collapse starts
  with the reward's shape.
- **The model team** owns the architecture-as-constant contract: the
  same `Transformer` class stays unmodified across missions so the
  comparison remains clean, and a model change is a new experiment, not
  a silent edit.
- **The evaluation owner** owns the per-seed outcome read (0.062-0.078
  across three seeds) that keeps the verdict from resting on one draw.

## Evidence boundary

The measured stage-01 config and the three recorded seed JSONs (200 steps
each, one board size, one reward). It reads those artifacts; it does not
re-train and does not claim the reward is un-fixable — stage 03's
diversity-direction attempt is exactly that question.

## Check your mental model

Answer each before opening it.

**1. How does a policy get format credit without ever reaching the goal?**

<details>
<summary>Answer</summary>

Because format credit only checks that the emitted characters are legal
moves. `RRRRRRRRRRRR` is all-legal, so it earns 1.0 format credit per
completion even though it never reaches the goal — and that credit is a
real gradient signal the policy optimizes. The terminal bit is drowned out
by the format credit the policy can earn for free, which is the mechanism
behind the collapse.

</details>

**2. Why is comparing against mission 01's decoder the right way to read
this?**

<details>
<summary>Answer</summary>

Because it controls the architecture. The policy is the same Transformer
class, same attention, same plumbing — only the objective changed. If the
collapse were an architecture problem, mission 01's identical network
would fail too; it does not, which isolates the reward's shape as the
variable the null result is about.

</details>

## Next

Back to [stage 01's GRPO run](../), or to
[the diversity direction](../../03-fixing-collapse/the-diversity-direction/)
which tries to fix the collapse the reward produced.
