---
status: verified
level: applied
base: scratch
label: When the reset never stops
verified: 2026-08-06
---

# Is a dead-code reset a cure, or a maintenance loop?

**Question:** [stage 05](../) resets dead codes and its recorded runs end
healthy — 64/64 usage in every seed. That raises a question the final
number hides: did the reset *cure* the codebook early, or does the training
loop keep paying the reset bill all the way through? The reset logs answer
it.

**Before this:** [stage 05's reset runs](../) and
[the codebook-collapse chapter](../../00-audio-codec/why-codebooks-collapse/)
that established the dead-code mechanism.

## The reset bill, measured

The analysis ([run record](runs/2026-08-06-reset-trajectory.md)) reads the
three recorded seeds' `reset_log`s:

| seed | total codes reset | first event | last event | final usage | MSE |
|---:|---:|---:|---:|---:|---:|
| 0 | 1,893 | step 50, 60 codes | step 2000, 1 code | 64/64 | 0.0187 |
| 1 | 1,848 | step 50, 60 codes | step 1950, 1 code | 64/64 | 0.0172 |
| 2 | 1,388 | step 50, 63 codes | step 1550, 1 code | 64/64 | 0.0173 |

The trajectory of seed 0's reset events per 200-step window:

| window | codes reset |
|---|---:|
| 0-200 | 180 |
| 200-1400 | 240-248 (sustained) |
| 1400-1600 | 221 |
| 1600-1800 | 14 |
| 1800-2000 | 3 |
| 2000-2200 | 1 |

## The reading

**The reset is a maintenance loop, not a cure.** Through roughly the first
1,400 of 2,000 steps, the codebook keeps dying and being revived at about
1.2 codes per step, sustained. The healthy 64/64 at the end is not a state
the codebook reached and stayed in; it is a steady state the training loop
is actively maintaining, and the maintenance only relaxes in the final
~400 steps (window resets fall 248 to 14 to 3 to 1).

**The codebook starts almost entirely dead.** Step 50's event resets 60-63
of 64 codes at once — the same near-total initial collapse the
codebook-collapse chapter measures at step 0, dragged out of the dead zone
by the reset rather than by the gradient. The mechanism and the rescue are
the same story told twice: dead codes get no straight-through gradient, so
the only way out is external intervention.

**The reset count is the cost the 2x2 exists to cut.** Stage 06's factorial
asks which half of the fix — reset, EMA, both, neither — actually does the
work. This chapter supplies the bill that comparison should reduce: if EMA
keeps codes alive, the total reset load should drop; if not, the reset is
doing the heavy lifting and the maintenance cost is the price of health.

## Evidence boundary

Three seeds, the stage's own recorded runs, 2,000 steps, synthetic clips.
It shows the reset is a sustained maintenance loop on this codec and that
health arrives only late in training; it does not compare reset against EMA
(stage 06's factorial does), does not measure a codebook that needs no
resetting, and does not claim the reset count generalizes across codec
configurations.

## Check your mental model

Answer each before opening it.

**1. "Final usage 64/64" reads like success. What does the reset log say the
number actually means?**

<details>
<summary>Answer</summary>

It means the codebook is healthy *at the moment of measurement*, after
1,800+ reset interventions across the run — a steady state the training loop
maintains, not a state the codebook reached on its own. One seed is still
resetting one code as late as step 2,000. The final number without the
trajectory overstates how stable the codebook is.

</details>

**2. Why does the reset bill stay near 248 codes per 200 steps for 1,400
steps and then collapse to single digits?**

<details>
<summary>Answer</summary>

Because early in training the codebook has no useful geometry — codes are
reset, reinitialized to random encoder outputs, and quickly die again as the
optimizer moves the encoder, so the loop churns. Late in training the
encoder and codebook settle into a stable partition, dead codes stop
forming, and the reset has almost nothing left to do. The collapse of the
reset bill is the signature of the codebook actually learning.

</details>

## Next

[Stage 06's 2x2](../../06-which-mechanism-did-it/): which half of the fix —
reset, EMA, or both — carries the health, against the reset bill this
chapter prices.
