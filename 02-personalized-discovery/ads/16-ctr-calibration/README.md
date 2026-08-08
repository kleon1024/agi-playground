---
status: verified
level: applied
base: scratch
label: pCTR calibration
verified: 2026-08-07
---

# The global calibration bar passes, but one slice overpays every auction

**Question:** eCPM ranking consumes pCTR inside the revenue estimate, so
a miscalibrated pCTR corrupts the auction. This stage measures
calibration error, then audits the operational symptom: the global
calibration bar passes while a traffic slice keeps overpaying eCPM. The
failure is a hidden slice, and the fix is stratified monitoring.

**Before this:** [stage 15 — eCPM ranking](../15-ecpm-ranking/) for where
pCTR is consumed, and [stage 04's fine-rank](../../shared/04-fine-rank/) for the
calibration discipline in ranking.

## The mechanism, executed

The run ([record](runs/2026-08-06-ctr-calibration.md)) measures a model
that predicts 0.50-0.59 but observes 3 clicks in 10:

| number | value |
|---|---|
| predicted range | 0.50-0.59 |
| observed | 3/10 |
| ECE | 0.2450 |

Calibration asks: of the impressions where the model predicted p, what
fraction actually clicked? The expected calibration error (ECE) bins the
predictions and averages the gap between predicted and observed rate per
bin. A calibrated model has ECE near zero — it says 0.55 and means 0.55.

## The failure mode, named and audited

**The aggregate passes, the slice fails.** The audit
([record](runs/2026-08-07-slice-calibration.md)) draws 20,000 impressions
(fixed seed): 18,000 on a calibrated desktop slice, 2,000 on a mobile
slice whose click rate is half the prediction:

| slice | share | ECE | mean predicted | mean observed |
|---|---:|---:|---:|---:|
| desktop | 90.0% | 0.0042 | 0.5003 | 0.4994 |
| mobile | 10.0% | 0.2303 | 0.4983 | 0.2680 |
| aggregate | 100% | 0.0238 | 0.5001 | 0.4763 |

The symptom is measured: aggregate ECE 0.0238 sits below a typical 0.05
alert bar, so a global monitor passes — while the mobile slice runs at
0.268 clicks against a mean prediction of 0.498, an overestimate of
nearly half. Every subsystem that consumes pCTR (eCPM, the auction, the
budget) inherits it. Stratifying by slice is how the case is found, and
per-slice monitoring needs enough impressions per slice to detect the
gap.

**A constant correction fixes the aggregate bias.** The
[when-the-correction-is-needed detour](when-the-correction-is-needed/)
applies the observed-to-predicted ratio (0.5505) and drops ECE from
0.2450 to 0.0000. The correction is the bridge from measurement to
deployment — but its shape matters: one multiplicative factor cannot fix
a bias that varies by slice.

**The fix itself goes stale.** The
[when-calibration-drifts detour](when-calibration-drifts/) refits nothing
and evaluates the same factor on a new window where the click rate rose
to 0.50: corrected ECE jumps to 0.3000, worse than the 0.0550 the raw
estimate carried. Calibration is a monitoring loop, not a one-time fit.

**Perfect order, wrong values.** The
[when-calibration-and-ranking-conflict detour](when-calibration-and-ranking-conflict/)
shifts every prediction up by 0.2 and shows the ranking unchanged while
every value is wrong — ordering and calibration are independent, and the
ads stack gates both.

## The fix and its trade

The fix is stratified monitoring plus a per-slice correction, because
the aggregate bar cannot see the slice that breaks: the audit's 20,000
impressions pass at aggregate ECE 0.0238 while the mobile slice runs at
0.2303 against a desktop 0.0042, and a constant correction fit on the
observed-to-predicted ratio (0.5505) drops the measured ECE from 0.2450
to 0.0000. The per-slice ECE is the case-finding instrument; the
correction is the bridge from measurement to deployment.

The trade is that the correction is a monitoring loop, not a one-time
fit. One multiplicative factor cannot fix a bias that varies by slice,
and a factor that is not refit expires: the same 0.5505 correction
evaluated on a new window where the click rate rose to 0.50 over-corrects
ECE to 0.3000, worse than the 0.0550 the raw estimate carried. And
calibration buys values, not order — shifting every prediction up by 0.2
leaves the ranking unchanged while every value is wrong — so the ads
stack gates both properties, and the measurement team owns the gap
between the correction's promise and fresh observations.

## Who owns the loop

The estimate only earns what someone is accountable for at each side of
the calibration loop, and each owner is tied to one of the failure modes
above:

- **The model and calibration team** owns the pCTR estimate and its
  correction: fitting on a rolling window and re-auditing per slice when
  the model or the traffic changes. It owns the hidden-slice and drift
  failures — the audit measured mobile ECE 0.2303 under an aggregate
  pass, and a stale factor that over-corrects to 0.3000 (Guo, Pleiss,
  Sun & Weinberger, 2017, ICML; Naeini, Cooper & Hauskrecht, 2015,
  AAAI).
- **The data and logging team** owns the impression stream that makes
  per-slice calibration possible: click labels with their slice
  attributes, joined to predictions at serving time. It owns the
  invisible-slice failure — a slice that cannot be stratified cannot be
  monitored, and the 0.2303 gap stays buried (Platt, 1999, fits the
  correction on logged data; Zadrozny & Elkan, 2002, KDD, show
  calibration is measured from labeled outcomes, which requires the log
  to carry the attributes).
- **The ads-measurement team** owns the calibration monitor: ECE by
  slice on a rolling window, with an alert on the gap between the
  correction's promise and fresh observations. It owns the
  aggregate-passes failure — the difference between 0.0238 and 0.2303
  is its standing check.

When the ownership is implicit, the model team certifies calibration on
aggregate, the logging team ships impressions without slice attributes,
and the mobile slice keeps overpaying eCPM until a revenue anomaly is
attributed to a model nobody re-audited per slice.

## Why this belongs in the mission

Mission 02's contract covers ads as a paid placement inside
recommendation and search. Calibration is where the model's probability
becomes the platform's revenue: eCPM, the auction, and budget pacing all
consume the same number, and all three break if it lies. The stage's
owner is the model team precisely because the ranking (stage 15) exposed
the estimate's value and this stage keeps it honest per slice.

## Evidence boundary

The executed ECE over ten hand-built predictions and the audit's 20,000
synthetic impressions (fixed seed) are illustrative and deterministic.
They demonstrate the measure and the hidden-slice arithmetic; they do not
model a real pCTR model's feature interactions, real click-log noise, or
the statistical confidence of a per-slice ECE, where monitoring uses
confidence bands and significance tests rather than single tables.

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

**2. Your global calibration monitor passes, but a market's revenue is
down. Where do you look?**

<details>
<summary>Answer</summary>

At ECE by slice, before the aggregate. The audit measured aggregate
0.0238 while the mobile slice ran at 0.2303 — a 90 percent calibrated
majority diluted a 10 percent broken slice. The aggregate bar passes
arithmetically; only stratification exposes which slice's clicks the
model overstates, and that slice is the one overpaying eCPM in every
auction it wins.

</details>

**3. What does a consistent 0.55-vs-0.30 gap tell you about the model?**

<details>
<summary>Answer</summary>

That it is systematically optimistic, not randomly wrong. A model with
ECE 0.2450 in one direction predicts too many clicks everywhere, which
means every ad's revenue is inflated in the same direction. A constant
shift like this is exactly what a calibration correction (Platt scaling
or isotonic regression) is designed to remove — the measured gap is the
input to the fix, and the drift detour is the reminder that the fix
expires.

</details>

## Next

Forward to [stage 17 — budget pacing](../17-budget-pacing/) where the
platform must deliver an advertiser's budget across the day.

A detour from here: [the fix that makes the estimate honest](when-the-correction-is-needed/) — the executed correction read: ECE 0.2450 -> 0.0000 from one scaling factor, the bridge from measurement to deployment.

Another detour: [the fix that made the estimate honest has an expiration date](when-calibration-drifts/) — the executed stale-fit read: the same factor that fixes the old window (0.0000) over-corrects the new one to 0.3000, worse than no fix.

A third detour: [perfect order, wrong values](when-calibration-and-ranking-conflict/) — the executed shift read: the model ranks clicks perfectly while every value is wrong by 0.2, so ordering and calibration are independent and the ads stack needs both.

Inside eCPM, an overestimated pCTR inflates the ad's revenue estimate, so
it wins the auction too often at a price based on a wrong number. The
platform over-delivers to underperforming ads, and the auction's payments
no longer match what the impressions earn. Calibration is therefore the
precondition of the entire ads stack: ranking (eCPM), pricing (auction),
and budget (pacing) all consume the same probability, and all three break
if it lies.
