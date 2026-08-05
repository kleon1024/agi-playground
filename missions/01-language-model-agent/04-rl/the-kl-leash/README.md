---
status: verified
level: applied
base: scratch
label: The KL leash
verified: 2026-08-06
---

# The leash that keeps the policy close

**Question:** [stage 04's GRPO](../) couples every token's update to a KL
toll against the frozen reference policy. What does that toll actually
compute, and why the k3 estimator instead of the naive difference?

**Before this:** [the group-relative trick](../the-group-relative-trick/) and
[stage 04's RL run](../).

## The leash, as arithmetic

The update per token is `-surrogate + kl_beta * kl`, where the KL term uses
Schulman's k3 estimator — `kl = exp(-d) + d - 1` with `d = new_logp -
ref_logp` ([run record](runs/2026-08-06-kl-leash.md)):

| new/ref | d | naive d | k3 KL | toll (beta 0.04) |
|---:|---:|---:|---:|---:|
| 0.5 | -0.693 | -0.693 | 0.307 | 0.012 |
| 1.0 | 0.000 | 0.000 | 0.000 | 0.000 |
| 2.0 | +0.693 | +0.693 | 0.193 | 0.008 |
| 3.0 | +1.099 | +1.099 | 0.432 | 0.017 |

<!-- interactive: KLLeach -->

## Two readings

**The k3 estimator is always non-negative; the naive difference is not.** At
new/ref 0.5 the naive d is -0.693 — a negative "KL" that would add
sign-flipping gradient to the update. k3 maps the same drift to +0.307, so
the leash only ever pushes toward the reference, never away. That is the
unbiased, always-non-negative property the stage's docstring names.

**The leash is asymmetric and soft.** Reducing probability mass costs more
than increasing it — half the probability costs 0.307, double costs 0.193,
at equal log-magnitude. And the toll at beta 0.04 stays small across the
range (max 0.045 at an extreme 0.3x drift): the leash is a soft constraint
that the update is free to pay, not a hard wall. The reference anchors the
policy; it does not freeze it.

## Evidence boundary

The arithmetic is `grpo.py`'s own, computed across the drift range; no model
was trained. It shows the estimator's properties and the toll's magnitude;
it does not measure how the leash changes a real GRPO run's trajectory —
that is the recorded RL runs' claim.

## Check your mental model

Answer each before opening it.

**1. Why does GRPO use the k3 estimator instead of the naive log-difference
as the KL toll?**

<details>
<summary>Answer</summary>

Because the naive difference can go negative — a new policy that assigns
more probability than the reference gives a negative "KL" — and a negative
KL toll pushes the update in the opposite direction of the constraint,
adding noisy sign-flipping gradient. k3 is an unbiased estimate that is
always non-negative, so the leash only ever restrains, never rewards drift.

</details>

**2. The toll is small (0.01-0.02 at beta 0.04). Why call it a leash at
all?**

<details>
<summary>Answer</summary>

Because its job is structural, not numerical: it makes the reference policy
a continuous anchor that any drift pays against, which is what separates
GRPO from the unconstrained surrogate. The small magnitude is the design —
a soft constraint the update can pay when the reward justifies it, rather
than a hard wall that would stop learning. The leash's strength is beta,
and beta is tunable; the leash's existence is what keeps the policy close.

</details>

## Next

Back to [stage 04's RL](../), or to
[mission 06's GRPO stages](../../../06-game-ai/01-grpo/) where the same
leash runs against a game's verifiable reward.
