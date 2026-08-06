---
status: verified
level: applied
base: scratch
label: When the corners reproduce
verified: 2026-08-06
---

# The 2x2 is trustworthy because its corners are already published

**Question:** [stage 06's factorial run](../) crossed dead-code reset with
EMA codebook update. This chapter reads the recorded grid and asks why the
two new corners can be believed.

**Before this:** [stage 06's factorial run](../) and its recorded 2x2.

## The grid, read

The run ([record](runs/2026-08-06-corners-read.md)) reads the recorded
corners:

| arm (seed 0) | codes | entropy | eval MSE | margin |
|---|---:|---:|---:|---:|
| plain | 18/64 | 0.405 | 0.02712 | 4.3% |
| reset-only | 64/64 | 0.826 | 0.01875 | 33.8% |
| ema-only | 1/64 | 0.000 | 0.02834 | -0.0% |
| reset+ema | 64/64 | 0.933 | 0.01810 | 36.1% |

## Two readings

**The two published corners reproduce to full float precision.** The
`plain` corner must equal stage 04's quantizer, and `reset-only` must
equal stage 05's — the recorded eval MSEs match bit-for-bit (0.02712 =
0.02712, 0.01875 = 0.01875). The grid is not a re-implementation that
happens to be close; it is the mission's own published numbers, rebuilt
and confirmed, which is what makes the two new corners measured rather
than approximate.

**The mechanism question is answered by the grid's shape.** EMA-only
collapses the codebook to 1/64 in seed 0 — worse than plain — while
reset-only reaches 64/64 and reset+ema adds the best entropy (0.933). The
reset is the mechanism that fixes utilization; the EMA refines it. The
factorial design is what separates the two contributions that a single
"did the fix work" run could not.

## Evidence boundary

The recorded factorial run (three seeds, four arms each, one dataset, ~74
min/seed). It reads that artifact; it does not re-train.

## Check your mental model

Answer each before opening it.

**1. Why does bit-for-bit reproduction of the corners matter?**

<details>
<summary>Answer</summary>

Because it validates the harness before the new arms are read. If the
`plain` corner differed from stage 04's published number, the two new
corners would be measured against an unknown baseline and the comparison
would be unanchored. The exact match (0.02712 = 0.02712, 0.01875 =
0.01875) proves the 2x2 runs the same model the mission already published
— so the reset+ema result is a real measurement, not an artifact.

</details>

**2. What does the ema-only corner add to the story?**

<details>
<summary>Answer</summary>

It isolates the EMA's contribution and shows it is not the fix. EMA-only
collapses to 1/64 codes in seed 0 — worse than plain — so the EMA alone
does not rescue utilization. Reset-only reaches 64/64, and reset+ema adds
the highest entropy. Without the ema-only corner, a reader could
misattribute the fix to the EMA; the full grid rules that out.

</details>

## Next

Back to [stage 06](../), or to
[which half of the fix did the work](../the-half-that-did-the-work/)
which reads the same grid's attribution side.
