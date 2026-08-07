---
status: verified
level: applied
base: scratch
label: When pCTR moves the rank
verified: 2026-08-06
---

# The knife-edge the click estimate sits on

**Question:** [stage 15's eCPM ranking](../) ranks by bid x pCTR. This
chapter reads the executed sweep and asks how sensitive the ranking is to
the click estimate.

**Before this:** [stage 15 — eCPM ranking](../) and its executed ranking.

## The sweep, executed

The run ([record](runs/2026-08-06-pctr-read.md)) sweeps Ad A's pCTR
(bid 2.00) against Ad B's fixed eCPM (150):

| Ad A pCTR | Ad A eCPM | winner |
|---:|---:|---|
| 0.03 | 60 | B |
| 0.05 | 100 | B |
| 0.07 | 140 | B |
| 0.09 | 180 | A |
| 0.11 | 220 | A |

## Two readings

**The ranking flips on a small pCTR change.** Ad B wins while Ad A's pCTR
is below 0.075; above it, Ad A's high bid takes over. A 2-point pCTR
change (0.07 -> 0.09) swaps the winner — the ranking is a knife-edge on
the click estimate.

**That knife-edge is why calibration is the precondition.** If pCTR is
systematically wrong (stage 16's 0.245 ECE), the ranking is optimized
against a wrong number and the wrong ad wins. The eCPM ranking is only as
good as the estimate feeding it, which is why calibration precedes
ranking in the ads stack, not follows it.

## Evidence boundary

The executed sweep over one ad pair (illustrative, deterministic). It
demonstrates the sensitivity; real rankings face the same knife-edge on
the full ad pool.

## The fix and its trade

The measured fix is to treat the flip point as a tolerance budget, not a
surprise. The stage audit quantified the stakes: a pCTR error that keeps
the true winner on top costs nothing, while an error large enough to flip
the winner costs 30-50 per impression. Calibration (stage 16) is the
instrument that keeps estimates inside the budget — histogram-binned
calibration with measured expected calibration error (Guo, Pleiss, Sun &
Weinberger, 2017, ICML; Naeini, Cooper & Hauskrecht, 2015, AAAI), or a
Platt-style temperature fit where the reliability curve is monotone
(Platt, 1999). The trade is on the estimator's side: the same
calibration that improves expected revenue can sacrifice ranking order
when the correction is uniform across the pool (Zadrozny & Elkan, 2002,
KDD), which is why the fix is to calibrate and then re-audit the ranking
with the realized column, not to calibrate and stop.

## Check your mental model

Answer each before opening it.

**1. Why does a lower-bid ad win at low pCTR for the other?**

<details>
<summary>Answer</summary>

Because eCPM is the product, not the bid. Ad B's 0.30 pCTR at bid 0.50
earns 150 per thousand; Ad A at pCTR 0.05 earns 100 despite the 2.00 bid.
Until Ad A's pCTR reaches 0.075, its expected revenue stays below Ad B's
— the platform earns more showing B, so B wins.

</details>

**2. What does the flip point tell you about the estimate's tolerance?**

<details>
<summary>Answer</summary>

That a 2-point pCTR error changes the winner. If Ad A's true pCTR is
0.08 but the model says 0.06, the ranking shows B when A would have been
more valuable — a small estimation error, a different allocation. The
flip point is the tolerance measure: it says how precisely pCTR must be
estimated for the ranking to be trustworthy.

</details>

## Next

Back to [stage 15](../), or to
[stage 16 — pCTR calibration](../../16-ctr-calibration/) which keeps the
estimate honest.
