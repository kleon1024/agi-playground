---
status: verified
level: applied
base: scratch
label: When the correction is needed
verified: 2026-08-06
---

# The fix that makes the estimate honest

**Question:** [stage 16's calibration](../) measures ECE but does not fix
it. This chapter reads the executed correction and asks what calibration
actually does to the estimate.

**Before this:** [stage 16 — pCTR calibration](../) and its executed ECE.

## The correction, executed

The run ([record](runs/2026-08-06-correction-read.md)) applies a
multiplicative correction to the miscalibrated estimate:

| number | value |
|---|---|
| mean predicted | 0.545 |
| observed | 0.300 |
| correction factor | 0.550 |
| ECE before -> after | 0.2450 -> 0.0000 |

## Two readings

**A single multiplicative correction removes the systematic bias.** The
model predicts 0.545 but observes 0.300; scaling every prediction by
0.55 (observed/predicted) makes the estimate honest, and ECE drops from
0.2450 to 0.0000. The correction is the calibration fix, and the
before/after is the measure of what it did.

**The correction is the bridge from measurement to deployment.** Stage 16
measures the error; this chapter applies the fix. In production the
correction is fit on a logged impression set (Platt scaling or isotonic
regression, learned rather than a single ratio), but the mechanism is the
same: find the systematic gap and remove it before the estimate feeds
eCPM, the auction, and the budget.

## Evidence boundary

The executed correction over one hand-built estimate (illustrative,
deterministic; a single multiplicative ratio, not a learned Platt fit). It
demonstrates the mechanism; real calibration fits the correction on
logged data.

## The fix and its trade

The measured fix is to fit the correction on logged impressions rather
than a single ratio, then verify on held-out data — temperature scaling
or Platt's logistic fit when the reliability curve is monotone (Platt,
1999, *Advances in Large Margin Classifiers*), bin-based calibration or
isotonic regression when it is not (Naeini, Cooper & Hauskrecht, 2015,
AAAI; Guo, Pleiss, Sun & Weinberger, 2017, ICML). The trade is
complexity versus capacity: a single multiplicative factor (this read's
0.5505) has one parameter and cannot fix a bias that varies by feature or
slice, which the stage audit's hidden-slice run demonstrates (mobile ECE
0.2303 against aggregate 0.0238) — while a per-bin fit fixes the slices
but needs enough logged impressions per bin to stay honest.

## Check your mental model

Answer each before opening it.

**1. Why is one scaling factor enough here?**

<details>
<summary>Answer</summary>

Because the error is systematic — the model overestimates by the same
ratio everywhere (0.545 vs 0.300). A single multiplicative correction is
exactly right for a constant-bias case: it maps the whole distribution
onto the observed rate. When the bias varies by region or feature,
production calibration fits a per-bin or per-feature correction instead
— the mechanism generalizes, the shape of the correction does not.

</details>

**2. What breaks if the estimate is used uncorrected?**

<details>
<summary>Answer</summary>

Every downstream consumer inherits the bias. eCPM ranking overestimates
revenue and shows the wrong ads; the auction prices them wrong; the
budget delivers to underperforming placements. One wrong probability,
three broken subsystems — which is why calibration is the precondition of
the ads stack, not a polish step.

</details>

## Next

Back to [stage 16](../), or to
[stage 17 — budget pacing](../../17-budget-pacing/) where the corrected
estimate feeds delivery.
