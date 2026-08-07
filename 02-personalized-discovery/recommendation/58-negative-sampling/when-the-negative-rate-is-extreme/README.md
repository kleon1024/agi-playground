---
status: verified
level: applied
base: scratch
label: When the negative rate is extreme
verified: 2026-08-07
---

# The 99% gradient that belongs to easy negatives

**Question:** [stage 58](../) downsamples negatives and corrects the rate.
This chapter asks why downsampling is necessary in the first place, and
answers: at extreme negative rates the easy negatives own the gradient even
when the model is still wrong.

**Before this:** [stage 58 — negative sampling](../).

## The gradient flood, executed

The run ([record](runs/2026-08-07-negative-rate-extreme.md)) reads the
gradient share at a 1:1000 positive-to-negative ratio:

| population | count | gradient share |
|---|---:|---:|
| positives | 100 of 100,100 | 1.0% |
| negatives | 10,000 of 100,100 | 99.0% |

## The reading

The negative class owns 99% of the gradient. Most of those negatives are
easy — the model is already right about them — but at this ratio their mass
still swamps the few positives, so the weights barely move toward the
signal. Downsampling negatives and correcting the rate is what gives the
positive signal a vote at all. The correction matters because the
downsample changes the base rate: rank order survives, calibration does not
(stage 58's own read).

## Evidence boundary

The executed gradient-share read over declared counts (illustrative,
deterministic). It demonstrates the imbalance; real systems must measure
the gradient share per class during training and tune the negative
sampling rate against the calibration check.

## Check your mental model

Answer each before opening it.

**1. Why do easy negatives dominate even when the model is wrong?**

<details>
<summary>Answer</summary>

Because of mass, not difficulty. At 1:1000 the negative class outnumbers
the positive class a hundred to one, so even small per-row gradients sum to
most of the update. The few positives cannot move the weights against that
tide.

</details>

**2. Why must the correction follow the downsample?**

<details>
<summary>Answer</summary>

Because the model learns the downsampled base rate, not the true one, which
inflates every probability. The ratio correction restores the true scale;
ranking metrics will not catch the break (stage 58's ECE does).

</details>

## Next

Back to [stage 58](../). The correction's own failure: [a wrong assumed
ratio lands the probabilities off on one side](../when-the-correction-overcorrects/).
