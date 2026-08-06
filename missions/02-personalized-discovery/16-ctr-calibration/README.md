---
status: verified
level: applied
base: scratch
label: pCTR calibration
verified: 2026-08-06
---

# The estimate must equal the click rate

**Question:** eCPM ranking uses pCTR inside the revenue estimate, so a
miscalibrated pCTR corrupts the auction. This stage measures calibration
error and shows why the estimate's honesty is an economic property, not a
statistical nicety.

**Before this:** [stage 15 — eCPM ranking](../15-ecpm-ranking/) for where
pCTR is consumed, and [stage 04's fine-rank](../04-fine-rank/) for the
calibration discipline in ranking.

## The miscalibration, executed

The run ([record](runs/2026-08-06-ctr-calibration.md)) measures a model
that predicts 0.50-0.59 but observes 3 clicks in 10:

| number | value |
|---|---|
| predicted range | 0.50-0.59 |
| observed | 3/10 |
| ECE | 0.2450 |

## The mechanism, named

Calibration asks: of the impressions where the model predicted p, what
fraction actually clicked? The expected calibration error (ECE) bins the
predictions and averages the gap between predicted and observed rate per
bin. A calibrated model has ECE near zero — it says 0.55 and means 0.55.

The measured 0.2450 is a systematic overestimate: the model says ~0.55,
the data says ~0.30. The gap is not noise; it is the same direction on
every prediction.

## Why this is an economic failure, not a metric

Inside eCPM, an overestimated pCTR inflates the ad's revenue estimate, so
it wins the auction too often at a price based on a wrong number. The
platform over-delivers to underperforming ads, and the auction's payments
no longer match what the impressions earn. Calibration is therefore the
precondition of the entire ads stack: ranking (eCPM), pricing (auction),
and budget (pacing) all consume the same probability, and all three break
if it lies.

## Evidence boundary

The executed ECE over one hand-built miscalibrated estimate
(illustrative, deterministic). It demonstrates the measure; real pCTR
calibration needs a large logged impression set and a correction fit
(e.g., Platt or isotonic).

## Check your mental model

Answer each before opening it.

**1. Why does ranking accuracy not fix calibration?**

<details>
<summary>Answer</summary>

Because ranking only needs the ordering of pCTR; calibration needs the
value. Two ads ranked correctly can still have systematically wrong
probabilities — one predicted 0.6 when it is 0.3, the other 0.4 when it
is 0.2. The ranking is unchanged, but the eCPM and the auction price are
both wrong. Calibration is a different property than discrimination, and
the ads stack consumes the number, not just the order.

</details>

**2. What does a consistent 0.55-vs-0.30 gap tell you about the model?**

<details>
<summary>Answer</summary>

That it is systematically optimistic, not randomly wrong. A model with
ECE 0.2450 in one direction predicts too many clicks everywhere, which
means every ad's revenue is inflated in the same direction. A constant
shift like this is exactly what a calibration correction (Platt scaling
or isotonic regression) is designed to remove — the measured gap is the
input to the fix.

</details>

## Next

Forward to [stage 17 — budget pacing](../17-budget-pacing/) where the
platform must deliver an advertiser's budget across the day.

A detour from here: [the fix that makes the estimate honest](when-the-correction-is-needed/) — the executed correction read: ECE 0.245 -> 0.000 from one scaling factor, the bridge from measurement to deployment.
