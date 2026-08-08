---
status: verified
level: applied
base: scratch
label: When the slice hides
verified: 2026-08-07
---

# The aggregate hides the slice; the slice's own noise hides the fix

**Question:** [stage 47's panel](../) catches the break that moves the
aggregate. This chapter asks what happens when the panel is built and
answers: a collapse confined to a small traffic segment is invisible in
the aggregate — and once you slice down to it, the segment's daily
signal is so noisy that the detection test either fires on noise or
waits for a lucky low day.

**Before this:** [stage 47 — monitoring and drift](../) and its executed
gap run, plus the slice panel in this stage's `prod/` path for the
instrument this detour's failure appears in.

## The small slice, executed

The run ([record](runs/2026-08-07-slice-hides-read.md)) gives three
segment sizes the same true 50% CTR drop at day 10 and measures a daily
z-test against a 14-day pooled test:

| segment | daily sd | daily detect | daily false alarms | pooled detect | pooled false |
|---|---:|---:|---:|---:|---:|
| 50k/day | 0.00088 | day 10 | 0 | day 23 | 0 |
| 5k/day | 0.00277 | day 10 | 0 | day 23 | 0 |
| 500/day | 0.00876 | day 13 | 2 | day 23 | 0 |

## The reading

The 500/day slice is where the drop lives and where the signal is
noisiest: its daily standard deviation (0.00876) is nearly half the
drop itself (0.020). The daily test fired twice on pre-drop noise and
detected the real drop three days late — three days of serving the
broken ranking, plus two pages' worth of false alerts. The pooled
14-day window detects reliably for every segment (day 23, the first day
a fully post-drop window exists) with zero false alarms, at the price of
latency.

The lesson is the trade, not the trick: on a small slice you cannot have
both low false alarms and fast detection. A tighter threshold does not
fix it — it only moves the failure from missed detections to pager
storms. The fixes that actually work change the sample size: pool
related segments to raise n, apply shrinkage toward the aggregate, or
accept the pooled window's latency for the slices that cannot be pooled.
The user-level version of the same problem — where a small segment
collapses without moving the page-level number — is why slice-aware
monitoring exists at all, and why the slice definition (which dimensions
you slice on) decides whether the collapse is findable.

## The fix and its trade

The fix is to change the sample size, not the threshold: pool related
segments to raise n, apply shrinkage toward the aggregate, or accept the
pooled window's latency for slices that cannot be pooled. The executed
simulation prices the failure — the 500/day slice carries the drop with
a daily standard deviation 0.00876, nearly half the 0.020 drop itself,
so the daily test fires twice on pre-drop noise and detects the real
drop at day 13, three days late; the pooled 14-day test detects at day
23 with zero false alarms for every segment. Tightening the threshold
only moves the failure from missed detections to pager storms.

The trade is latency against reliability: pooling shrinks the standard
deviation by the square root of the window (0.00876 over sqrt(14) is
0.00234, turning a 2.3-sigma event into an 8.5-sigma one) and pays
detection latency, never signal. A tighter daily threshold pays
reliability for noise without gaining signal. And the slice definition
itself — which dimensions the panel slices on — is the upstream
decision that decides whether the collapse is findable at all, so the
monitoring team owns that choice as carefully as the threshold.

## Who owns the loop

- **The monitoring team** owns the slice definitions and the pooling
  dimensions, the decision that decides whether a collapse is findable.
- **The data and analytics team** owns the shrinkage and pooled
  estimators that raise effective sample size on small slices.
- **The on-call operator** accepts the pooled window's latency for
  slices that cannot be pooled, since the trade is theirs to live with
  during the incident.

## Evidence boundary

The executed simulation over three declared segment sizes (illustrative,
deterministic, seeded). It demonstrates the statistics of small slices;
real systems must measure their own per-slice noise, set thresholds
against it, and choose pooling dimensions that match the business
decision the alert is protecting.

## Check your mental model

Answer each before opening it.

**1. Why does the 500/day slice fire on noise before the drop?**

<details>
<summary>Answer</summary>

Because its daily standard deviation is 0.00876, so a single day's
estimate routinely lands more than 1.96 standard deviations from the
mean — the z-test's 5% false-alarm rate is real, and on a small slice
the noise it guards against is a large share of the signal. Two of those
pre-drop days crossed the threshold before day 10.

</details>

**2. Why does pooling change the trade instead of just delaying it?**

<details>
<summary>Answer</summary>

Because the pooled test's standard deviation shrinks by the square root
of the window length — 0.00876 / sqrt(14) = 0.00234 — so the same drop
is an 8.5-sigma event instead of a 2.3-sigma one. The detection becomes
reliable, and the false-alarm rate falls with the noise; what the pooled
test pays is latency, not reliability. Tightening a daily threshold
pays reliability for noise without ever gaining signal.

</details>

## Next

The panel and its thresholds are built; [stage 48 — realtime user
state](../../48-realtime-user-state/) asks what state should ride on the
request path itself, where the latency budget this detour measured
becomes the product's own budget.
