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

## The fix and its trade

The fix is to filter or reweight the labels instead of trusting them:
filtering removes suspicious labels before training, and reweighting
down-weights them during it, both driven by agreement checks on the
labeling side. The executed flip prices the failure — the flipped pair
sets a 0.80 loss against 0.09 combined for the clean pairs, a 0.89
total floor, because every update on the flipped pair moves the model
toward the wrong preference and no amount of clean data cancels a
wrong gradient that keeps repeating.

The trade is that both repairs cost signal: filtering risks removing a
true preference that merely looked odd, and reweighting down-weights
correct labels along with the wrong ones. The floor is structural —
the frontier cost of RLHF is label quality, not model capacity — so the
pipeline has to price the filter's false-removal risk against the
wrong-gradient floor it removes, with the labeling process and a
measured noise model as the inputs to that decision.

## Who owns the loop

- **The labeling and annotation team** owns the pairs, the agreement
  checks that catch flipped labels, and the re-ask policy for
  low-margin preferences.
- **The ranking and model team** owns the filter-or-reweight policy
  that keeps a flipped pair from setting the loss floor.
- **The evaluation team** owns the noise model and the measured
  robustness that prices the filter's false-removal risk.

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
