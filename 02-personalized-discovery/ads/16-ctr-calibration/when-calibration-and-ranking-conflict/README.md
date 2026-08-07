---
status: verified
level: applied
base: scratch
label: When calibration and ranking conflict
verified: 2026-08-06
---

# Perfect order, wrong values

**Question:** [stage 16's calibration](../) measures ECE. This chapter
reads the executed conflict between ranking quality and calibration and
asks what each metric actually certifies.

**Before this:** [stage 16 — pCTR calibration](../) and its executed ECE.

## The conflict, executed

The run ([record](runs/2026-08-06-conflict-read.md)) builds a model that
ranks four items identically while predicting every value shifted up by
0.2:

| number | value |
|---|---|
| true probabilities | [0.20, 0.40, 0.60, 0.80] |
| predicted | [0.40, 0.60, 0.80, 1.00] |
| ranking match | identical order |
| mean calibration error | 0.20 |

## Two readings

**Ordering and values are independent properties.** The shifted model
ranks clicks perfectly — the order is unchanged — while every value is
wrong by 0.2. A check that only compares order certifies this model,
though it is wrong everywhere. Ranking quality and calibration error move
separately, which is why neither metric can stand in for the other.

**The two properties serve different consumers.** The ranker consumes
order; eCPM, the auction, and the budget consume the values. A
perfectly-ordered miscalibrated model delivers the right ads in the wrong
order of economic value — the platform shows B over A (stage 15) using
numbers that overstate what the clicks are worth. That is why the ads
stack needs both gates: calibration for the values, ranking for the
order.

## Evidence boundary

The executed shifted model over four hand-built probabilities
(illustrative, deterministic). It demonstrates the independence; real
models fail ordering and calibration in different mixes, which is exactly
why both must be measured.

## Check your mental model

Answer each before opening it.

**1. How can the ranking be perfect and the model still be wrong?**

<details>
<summary>Answer</summary>

Because a constant shift preserves order. Every prediction is the true
probability plus 0.2, so the ordering of items is unchanged while the
values all overstate the click rate. The ranker sees the same relative
winner; the auction and the budget see numbers that are uniformly too
high. The order says which item wins; the values say what the win is
worth, and the model is wrong about the second while being right about
the first.

</details>

**2. Which subsystems inherit the 0.2 error?**

<details>
<summary>Answer</summary>

Every consumer of the values: eCPM ranking multiplies the inflated pCTR
into revenue, the auction prices the win from it, and budget pacing
spends against it. Only the ordering survives, because it is
shift-invariant. Calibration is the gate that stops the inflated values
from reaching those consumers — which is why the stage places it before
ranking, not after.

</details>

## Next

Back to [stage 16](../), or to
[stage 17 — budget pacing](../../17-budget-pacing/) where the corrected
estimate feeds delivery.
