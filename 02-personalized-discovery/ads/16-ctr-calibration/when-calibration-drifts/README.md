---
status: verified
level: applied
base: scratch
label: When calibration drifts
verified: 2026-08-07
---

# The fix that made the estimate honest has an expiration date

**Question:** [stage 16's correction detour](../when-the-correction-is-needed/)
fits one multiplicative factor and drops ECE to 0.0000. This chapter
reads the executed stale-correction audit and asks what happens when the
click rate moves after the fit.

**Before this:** [stage 16 — pCTR calibration](../) and its correction
detour.

## The drift, executed

The run ([record](runs/2026-08-07-stale-correction.md)) fits the factor
on an old window (click rate 0.30), then evaluates it on a new window
where the rate has risen to 0.50:

| window | ECE, raw estimate | ECE, stale correction applied |
|---|---:|---:|
| old (fit window) | 0.2450 | 0.0000 |
| new (rate rose to 0.50) | 0.0550 | 0.3000 |

## Two readings

**The correction works where it was fit, then over-corrects.** The factor
0.5505 maps the old window's 0.545 predictions onto its 0.30 observed
rate exactly. On the new window the model still predicts ~0.545 but the
market now clicks at 0.50 — the raw estimate is already close (0.0550),
and the stale factor pushes it to 0.3000. The fix itself becomes the
failure, worse than no fix at all.

**Calibration is a monitoring loop, not a one-time fit.** A multiplicative
factor (or a Platt temperature, or an isotonic map) is a point estimate
of a rate that moves with the market, the audience, and the season. The
production question is not "did the fit work" but "is the fit still
current" — which is answered by watching ECE on new traffic and refitting
on a rolling window when it crosses the alert bar (Guo, Pleiss, Sun &
Weinberger, 2017, ICML, refit on validation data and warn that
distribution shift invalidates the fit; Naeini, Cooper & Hauskrecht,
2015, AAAI, for bin-based calibration and its limits).

## The fix and its trade

The measured fix has two parts. Refit the correction on a rolling window
so the factor tracks the rate (Platt, 1999, fits a monotone transform to
current data; the same principle holds for a logit or isotonic fit), and
monitor per-window ECE on fresh traffic as the drift detector — the
0.0550-to-0.3000 jump is the alarm the stale fit needs to raise. The
trade is on the refit cadence: a short window tracks the market but
overfits its noise and churns the correction, a long window is stable
but lags the shift. The executed read shows the failure that motivates
the choice — a factor that is never refit converts a calibration fix
into a new, larger bias.

## Evidence boundary

The executed read uses hand-built predictions and click vectors with no
random draws (illustrative, deterministic). It demonstrates the
over-correction mechanism; real drift detection fits on logged windows
with confidence bands and alarms on statistically significant ECE
movement, not on a single table.

## Check your mental model

Answer each before opening it.

**1. How can the fix make the estimate worse than doing nothing?**

<details>
<summary>Answer</summary>

Because the factor encodes a rate that moved. The fit multiplied every
prediction by 0.55 to correct a 0.30 click rate; when the rate rises to
0.50 the same factor drags the estimate to 0.30 — further from truth
than the raw 0.545 was. The correction is right about the past window
and wrong about the present, and nothing in the factor itself knows the
difference.

</details>

**2. Where does the drift alarm live, and what does it watch?**

<details>
<summary>Answer</summary>

In the calibration monitor, watching ECE on fresh traffic by slice.
The executed table is the template: when corrected ECE on the new window
exceeds the raw estimate's ECE, the fit has gone stale and must be
refit. The alarm is the gap between what the correction promises and
what new data observes — the same measurement that first caught the
miscalibration, re-run continuously.

</details>

## Next

Back to [stage 16](../), or to
[stage 17 — budget pacing](../../17-budget-pacing/) where the corrected
estimate feeds delivery.
