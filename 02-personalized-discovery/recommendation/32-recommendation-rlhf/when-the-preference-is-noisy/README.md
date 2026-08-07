---
status: verified
level: applied
base: scratch
label: When the preference is noisy
verified: 2026-08-07
---

# The preference label is noisy and sets a loss floor

**Question:** [stage 32's preference optimization](../) learns from
pairwise labels. This chapter reads the executed flip and asks what one
wrong label costs.

**Before this:** [stage 32 — recommendation RLHF](../) and its executed
Bradley-Terry loss.

## The flip, executed

The run ([record](runs/2026-08-07-preference-is-noisy-read.md)) flips
one of three preference labels:

| chosen | rejected | loss | flipped |
|---|---:|---:|---|
| 1.2 | 0.4 | 0.00 | no |
| 0.9 | 0.8 | 0.09 | no |
| 0.3 | 1.1 | 0.80 | yes |

Total loss floor: 0.89.

## The reading

The flipped pair — where the rejected item scores higher — forces the
model to push scores the wrong way, and its 0.80 loss dominates the
total. The clean pairs contribute only 0.09 combined; the floor the
noise sets cannot be removed by more clean data, because every update
on the flipped pair moves the model toward the wrong preference. Real
RLHF labels are noisy, so the pipeline has to filter or reweight — the
frontier cost is label quality, not model capacity.

## Evidence boundary

The executed loss over one declared flip (illustrative, deterministic,
assumed scores). It demonstrates the mechanism; real preference noise
needs the labeling process, a noise model, and measured robustness,
which a trained policy would show.

## Check your mental model

Answer each before opening it.

**1. Why can the clean pairs not undo the flipped pair?**

<details>
<summary>Answer</summary>

Because optimization is per-example: each pair contributes its own
gradient. The flipped pair's gradient pushes the model to rank the
rejected item higher, and no amount of correct pairs cancels a wrong
update that keeps repeating — the clean pairs have their own small
losses (0.09 total) while the flip's 0.80 loss dominates every step.
The floor is structural, not a tuning issue.

</details>

**2. What does the pipeline have to do instead of trusting the
labels?**

<details>
<summary>Answer</summary>

Filter or reweight. Filtering removes suspicious labels before
training; reweighting down-weights them during it. Both are data
quality decisions — the frontier cost of RLHF is label quality, not
model capacity. A model trained on the flipped set would learn the
wrong preference and no architecture change would fix it, which is the
detour's point.

</details>

## Next

Back to [stage 32](../). The
[reward-gaming detour](../when-the-reward-is-gamed/) shows the second
RLHF failure: even correct labels can be gamed by the policy that
maximizes the proxy.
