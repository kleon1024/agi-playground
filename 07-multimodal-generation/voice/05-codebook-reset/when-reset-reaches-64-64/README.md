---
status: verified
level: applied
base: scratch
label: When reset reaches 64/64
verified: 2026-08-06
---

# The mechanism that fixed utilization in every seed

**Question:** [stage 05's codebook reset](../) applied a dead-code reset
to the 10-speaker codec. This chapter reads the recorded JSONs and asks
what the reset actually changed.

**Before this:** [stage 05's codebook reset](../) and its recorded JSONs.

## The before/after, read

The run ([record](runs/2026-08-06-reset-read.md)) reads the recorded
seeds:

| seed | codes used (reset) | entropy ratio | resets performed |
|---|---:|---:|---:|
| 0 | 64/64 | 0.826 | 1,893 |
| 1 | 64/64 | 0.814 | 1,848 |
| 2 | 64/64 | 0.791 | 1,388 |

Stage 04 without reset: 18, 63, 32 of 64.

## Two readings

**The reset reaches 64/64 in every seed.** Stage 04's seed-dependent
utilization (18/63/32) is gone: all three seeds now use every codebook
entry, with entropy ratios 0.79-0.83. The mechanism does exactly what it
is supposed to — dead codes are detected (threshold 1.0) and reset every
50 steps, and the utilization gap closes in every seed, not just the
lucky ones.

**The resets are the mechanism's signature, and they taper.** Each seed
performs thousands of resets early (1,893 / 1,848 / 1,388), and the
reset log shows the count declining as the codebook stabilizes — early
steps reset heavily, later steps almost not at all. The taper is the
evidence the reset is a maintenance loop, not a constant scramble: it
fixes the codebook and then mostly stops being needed.

## The fix and its trade

The fix is the dead-code reset itself: codes whose EMA count falls below
the threshold (1.0) are reinitialized every 50 steps, and the measured
before/after closes the seed-dependent gap — 64/64 codes in every seed (vs
stage 04's 18/63/32), entropy 0.79-0.83, margins tightening to the
33.8%-37.6% band. The trade is that the mechanism's signature is also its
cost: 1,893/1,848/1,388 resets per run, front-loaded early and tapering as
the codebook stabilizes — which is exactly why the healthy final number
reads as a maintained steady state rather than a cure (the sibling chapter
prices that bill), and why 64/64 usage is a utilization claim, not a
quality score.

## Who owns this loop

- **The codec owner** owns the reset mechanism and its threshold contract
  (every 50 steps, below 1.0); the reset log is part of the run record, so
  the mechanism's work is verifiable, not inferred.
- **The eval owner** owns the before/after read: the same recipe as stage
  04 with only the quantizer changed, which is what isolates the mechanism
  as the one variable under test.
- **The mission owner** owns the maintenance-cost boundary: the taper (early
  churn, late quiet) is reported so the reset's price is visible, and
  stage 06's 2x2 exists to test whether EMA halves that bill.

## Evidence boundary

The recorded reset-codec JSONs (three seeds, same recipe as stage 04, only
the quantizer differs). It reads those artifacts; it does not re-train.

## Check your mental model

Answer each before opening it.

**1. Why does the reset fix utilization when more training did not?**

<details>
<summary>Answer</summary>

Because it attacks the mechanism directly. Stage 04's seed-dependence is
the softmax router concentrating on a few codes and the dead ones never
being chosen again — more training does not unstick them. The reset
detects codes below the dead threshold and reinitializes them, which is
the one intervention that makes the unused entries usable again.

</details>

**2. What does the reset count tell you about the cost?**

<details>
<summary>Answer</summary>

That the mechanism is cheap and self-limiting. Thousands of resets happen
early, when the codebook is unstable, and taper to near-zero as it
stabilizes — the log shows the maintenance load falling off. The cost is
not a constant tax; it is front-loaded into the phase where it is needed,
which is why the reset is a practical fix rather than a research toy.

</details>

## Next

Back to [stage 05](../), or to
[is a dead-code reset a cure, or a maintenance loop](../when-the-reset-never-stops/)
which reads the same run's cost side.
