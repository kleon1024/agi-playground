---
status: verified
level: applied
base: scratch
label: When attribution overcounts
verified: 2026-08-07
---

# The measurement model decides which channel gets the budget

**Question:** [stage 30's ads measurement](../) measures the ad by what
it changed. This chapter reads the executed attribution comparison and
asks what a last-click model overcounts.

**Before this:** [stage 30 — ads measurement](../) and its executed
incrementality model.

## The overcount, executed

The run ([record](runs/2026-08-07-attribution-overcount-read.md))
credits one conversion with three touchpoints:

| model | search ad | display ad | email |
|---|---:|---:|---:|
| multi-touch shares | 0.4 | 0.2 | 0.4 |
| last-click | 0.0 | 0.0 | 1.0 |

Last-click overcount: 0.6.

## The reading

Last-click gives the final touchpoint the whole conversion, crediting
email with 0.6 of value it shared. The measurement model decides which
channel gets the budget — an overcounting model misallocates spend even
when the ads work. The ads may be perfectly effective and the report
still routes next quarter's budget to the wrong channel, because the
measurement, not the campaign, produced the credit.

## The fix and its trade

The fix is to treat attribution as a measurement model with a ground
truth: run incrementality experiments on a sample of spend, measure
which touchpoints actually move conversions, and calibrate the
attribution weights to that measured credit instead of the last-click
default. The trade is that incrementality experiments are exactly the
expensive, low-power measurement [stage 30's audit](../) quantified —
the 0.4-point increment needs 28,547 users per arm at 80% power — so
the weights can only be re-measured occasionally and on a slice of the
budget, and the model drifts in between (Dalessandro et al., 2012,
arXiv:1209.2664, show causal attribution models can recover
touchpoint effects from randomized data). The alternative — keep
last-click because it is simple and auditable — is the failure the
detour measured: 0.6 of credit misplaced, next quarter's budget
routed to the wrong channel, and no experiment to correct it.

## Evidence boundary

The executed credit comparison over one conversion with declared shares
(illustrative, deterministic). It demonstrates the mechanism; real
attribution also needs the actual touchpoint data and a model choice,
which is why incrementality experiments are the ground truth for
attribution models.

## Check your mental model

Answer each before opening it.

**1. Why does the last-click model misallocate budget even when the ads
work?**

<details>
<summary>Answer</summary>

Because it ignores the earlier touchpoints entirely. The search and
display ads contributed 0.6 of the credit, but last-click gives all 1.0
to email. The next budget follows the credit, so the channels that
actually caused the conversion get defunded in favor of the final
touchpoint — the measurement error becomes a spend error.

</details>

**2. What is the ground truth attribution models should be checked
against?**

<details>
<summary>Answer</summary>

Incrementality (stage 30's method): a holdout experiment that measures
what each channel actually caused. Attribution models are estimates
over observed touchpoints; incrementality is the control-group
measurement of the same effect. Where the two disagree, the
experiment is the truth and the model is the bias to fix.

</details>

## Next

Back to [stage 30](../), which measures the ad by what it changed. The
[zero-lift detour](../when-the-incrementality-is-zero/) shows the null
result the same discipline exists to find.
