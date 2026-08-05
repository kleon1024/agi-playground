---
status: verified
level: applied
base: scratch
label: The half that did the work
verified: 2026-08-06
---

# Which half of the fix did the work?

**Question:** [stage 06](../) crossed dead-code reset with the EMA codebook
update in a 2x2 factorial. The codebook-health line (the collapse, reset,
and multi-speaker chapters) made the question; this chapter reads the
recorded grid for the answer.

**Before this:** [stage 06's factorial run](../) and the codebook-health
chapters.

## The grid, read

The run ([record](runs/2026-08-06-factorial-grid.md)) reads the three
seeds' four arms:

| arm | seed 0 MSE | seed 1 MSE | seed 2 MSE |
|---|---:|---:|---:|
| plain | 0.0271 | 0.0170 | 0.0212 |
| reset-only | 0.0187 | 0.0172 | 0.0173 |
| ema-only | 0.0283 | 0.0275 | 0.0275 |
| reset+ema | 0.0181 | 0.0168 | 0.0205 |

Recorded main effects (seed 0): reset without EMA -0.0084 MSE (+46 codes);
EMA without reset +0.0012 MSE (-17 codes).

## Two readings

**The reset did the work; EMA alone made things worse.** Reset-only beats
plain in two seeds and ties the third (which was already healthy), and its
main effect is a large improvement (-0.0084 MSE, +46 codes). EMA-only is
worse than plain in all three seeds — the recorded effect is -17 codes and
worse MSE. The mechanism that fixed the seed-dependent collapse is the
reset, not the EMA.

**EMA is an enhancer, not a fixer.** The reset+ema corner is the best
(0.0181/0.0168/0.0205), marginally ahead of reset-only — the EMA smooths
the codebook update on top of the reset, and only there. The 2x2 answer is
unambiguous across seeds: the reset carried the work, and the EMA's value
is conditional on the reset existing.

## Evidence boundary

Three seeds, the stage's recorded factorial; the main effects are the
recorded seed-0 numbers. It reads the grid and the main effects; it does
not re-train, and it does not generalize the answer beyond this codec
configuration.

## Check your mental model

Answer each before opening it.

**1. EMA alone is worse than plain in every seed. Why would a standard
codebook fix actively hurt?**

<details>
<summary>Answer</summary>

Because EMA is a smoothing of the codebook update, not a recovery
mechanism — it slows the codebook's movement, and on a codebook whose
collapse is driven by dead codes, smoothing alone leaves the dead codes
dead while dampening the healthy ones' adaptation. The recorded effect
(-17 codes) is the smoothing reducing the codebook's usable spread without
rescuing anything. The EMA's benefit appears only when the reset has
already restored the dead codes, which is why it is an enhancer.

</details>

**2. The reset+ema corner is only marginally better than reset-only. What
does that say about where the fix's credit belongs?**

<details>
<summary>Answer</summary>

That the credit belongs almost entirely to the reset: reset-only closes
most of the gap, and EMA adds a small, conditional improvement. The 2x2 is
precisely the design that assigns credit — if only one mechanism had been
tested, either the reset alone (over-attributing to it) or the pair (over-
attributing to the EMA) would have misread the answer. The grid shows the
reset carried the work and the EMA is a marginal enhancement.

</details>

## Next

Back to [stage 06's factorial](../../06-which-mechanism-did-it/), or to
[the codebook-collapse chapter](../../00-audio-codec/why-codebooks-collapse/)
where the failure this fix addresses was first measured.
