---
status: verified
level: applied
base: scratch
label: When silence is a local minimum
verified: 2026-08-06
---

# The collapse that looked like success

**Question:** [stage 00's codec training](../) recorded a first attempt
that plateaued at the silence baseline. This chapter reads the recorded
pilot and asks why the collapse happened and how the escape worked.

**Before this:** [stage 00's audio codec](../) and its recorded training.

## The collapse, read

The run ([record](runs/2026-08-06-silence-minimum.md)) reads the recorded
pilot:

| signal | value |
|---|---|
| recon MSE at plateau | 0.325 (silence baseline) |
| codebook usage | 1-2 of 64 codes |
| escape | loss drops 0.32 -> 0.03 once the decoder leaves the minimum |

## Two readings

**Against a zero-mean signal, silence is locally optimal.** The decoder's
first 60-90 steps sit in a genuine local minimum where outputting
near-silence minimizes MSE — the signal averages to zero, so doing nothing
looks right. The VQ commitment loss collapses with it (the codebook stops
being used). The pilot is the evidence that this is a real minimum, not a
hyperparameter miss: the loss is genuinely low, and nothing is learning.

**The escape is why the recipe matters as much as the loss.** The decoder
leaves the minimum only once gradient noise pushes it toward reproducing
the waveform's shape — after which loss drops sharply (0.32 -> 0.03 over
the next 150 steps). Higher LR and longer training are what get the
decoder out; a lower LR would have stayed stuck. The recorded before/after
is the argument for the training recipe, not just the architecture.

## Evidence boundary

The recorded codec training run (one pilot, one escape, synthetic tone
clips). It reads that artifact; it does not re-train and the plateau
characterizes this task's zero-mean signal.

## Check your mental model

Answer each before opening it.

**1. Why does the loss look healthy while the codec is broken?**

<details>
<summary>Answer</summary>

Because the loss is minimized by doing nothing. The signal is zero-mean,
so a silence-matching decoder achieves low MSE without ever using the
codebook — the VQ commitment loss collapses toward zero alongside it. A
loss-only read reports "training is working"; the codebook-usage counter
(1-2 of 64) is the number that says the codec is collapsed.

</details>

**2. What does the escape say about fixing a codebook collapse?**

<details>
<summary>Answer</summary>

That the collapse is a local minimum, so the fix is getting the model out
of it — higher LR, longer training, or a different escape mechanism —
not changing the loss. The recorded drop (0.32 -> 0.03) shows the decoder
is capable once it leaves; the problem is the exit, and the recipe is
what buys it.

</details>

## Next

Back to [stage 00](../), or to
[why a VQ codebook collapses](../why-codebooks-collapse/) which reads the
same stage's collapse anatomy.
