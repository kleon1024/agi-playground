---
status: verified
level: applied
base: scratch
label: When the retention window truncates
verified: 2026-08-07
---

# The observed window decides the channel verdict

**Question:** [stage 55's unit economics](../) priced users by retention
times revenue. This chapter asks what happens when the platform has not
watched the cohort long enough, and answers: LTV is measured on an
observation window, the window truncates the cohort's curve, and a
slowly-ramping channel looks weak at three months and dominant at
twenty-four — so the window you measured, not the channel's economics,
decides the verdict.

**Before this:** [stage 55 — LTV and CAC](../) for the ratio being
measured, and [the retention that
flattens](../when-retention-flattens/) for the sticky tail this window
misses.

## The truncation, executed

The run ([record](runs/2026-08-07-retention-window-read.md)) compares
each channel's 3-month observed LTV against its true 24-month value:

| channel | 3-month view | true 24m | 3m ltv/cac | true ltv/cac |
|---|---:|---:|---:|---:|
| paid installs | \$7.05 | \$7.78 | 0.88 | 0.97 |
| referral | \$3.10 | \$47.10 | 0.78 | 11.78 |

## The reading

At three months paid installs looks like the better bet (0.88 vs 0.78):
its curve is fully visible because it decays immediately. Referral looks
weak because its users ramp slowly — the truncated window sees only the
ramp, not the flat 0.42 tail, so its 3-month LTV/CAC is 0.78 against a
true 11.78. A team that reads the window and stops ranks the wrong
channel. The classic fix is to model the retention curve from
recency-frequency data rather than reading a truncated window as the
truth (Fader, Hardie & Lee, "Counting Your Customers the Easy Way",
Marketing Science 2005), and customer valuation depends exactly on
getting this horizon right (Gupta, Lehmann & Stuart, "Valuing
Customers", Journal of Marketing Research 2004).

The production tell is a channel review that keeps promoting fast-decay
channels: the review is reading windows, not curves. The fix is to
report LTV/CAC per horizon and to model the curve's shape — especially
the ramp and the tail — before scaling any acquisition spend.

## Evidence boundary

The executed comparison over two declared 24-month retention curves
(illustrative, deterministic). It demonstrates the mechanism; real unit
economics must measure each channel's own curve per cohort and state the
horizon, because the window is a modeling choice that flips the verdict.

## Check your mental model

Answer each before opening it.

**1. Why does paid installs look better at 3 months when referral is
worth more overall?**

<details>
<summary>Answer</summary>

Because paid installs' curve is fully visible at three months — it
decays from month one, so the window has already seen the whole story —
while referral's users are still ramping. The 3-month window captures
referral before its retention has peaked, so the observed LTV is a
fraction of the true value. The window does not hide paid installs'
truth; it simply cannot see referral's yet.

</details>

**2. How would you stop this from deciding a channel review?**

<details>
<summary>Answer</summary>

By requiring the horizon in every LTV number and modeling the curve's
shape — ramp, decay, and tail — instead of reading the observed months
as the truth. A fast-decay channel's windowed and true numbers agree;
the gap between them is itself the diagnostic. If a channel's LTV/CAC
keeps climbing as the window grows, the review should be reading the
curve, not the snapshot.

</details>

## Next

Back to [stage 55](../). The unit economics hold once the horizon is
named; the loop closes here — every stage from 43 to 55 is now read
through the same aggregate-vs-slice discipline that this detour applies
to the retention window.
