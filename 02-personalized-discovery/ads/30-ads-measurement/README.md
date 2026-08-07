---
status: verified
level: applied
base: scratch
label: Ads measurement
verified: 2026-08-07
---

# The lift that paid for the campaign is invisible to the experiment that measured it

**Question:** every ads stage so far optimized what the platform
controls. This stage asks how anyone knows the ad worked, and answers:
by incrementality — the exposed group's outcome minus the control
group's, the part the ad actually caused. The audit then asks the
industrial question the arithmetic skips: is that increment even
visible to an experiment at the sample sizes a campaign can buy?

**Before this:** [stage 24 — search measurement](../../search/24-search-measurement/)
for the measurement discipline, and [stage 27 — bid strategy](../27-bid-strategy/)
for the advertiser whose budget the measurement decides.

## The lift, executed

The run ([record](runs/2026-08-07-ads-measurement.md)) compares exposed
and control conversion rates:

| group | conversion rate |
|---|---:|
| exposed | 0.032 |
| control | 0.028 |
| lift | 14.3% |
| increment | 0.4 points |

The increment is the number that matters: 0.028 of the exposed users
would have converted without the ad, so the ad's actual effect is 0.4
points, not the 0.032 the raw click rate shows. That difference is the
entire reason the [overcount detour](when-attribution-overcounts/) and
the [zero-lift detour](when-the-incrementality-is-zero/) exist.

## The failure mode, named and audited

**The increment is buried in binomial noise.** The audit
([record](runs/2026-08-08-lift-power.md)) simulates conversion noise
(fixed seed) around the stage's own rates — exposed 0.032, control
0.028 — and sweeps the sample size per arm:

| n per arm | observed increment | 95% CI | p | the CI excludes zero? |
|---:|---:|---|---|---|
| 2,000 | +0.0070 | -0.0029 to +0.0169 | 0.164 | no |
| 8,000 | +0.0000 | -0.0052 to +0.0052 | 1.000 | no |
| 20,000 | +0.0036 | +0.0002 to +0.0069 | 0.040 | yes |
| 50,000 | +0.0034 | +0.0013 to +0.0055 | 0.001 | yes |
| 200,000 | +0.0043 | +0.0033 to +0.0054 | <0.001 | yes |
| 1,000,000 | +0.0038 | +0.0033 to +0.0042 | <0.001 | yes |

The verdict is measured: at 8,000 users per arm the observed lift is
literally 0.0000 and the CI covers zero — the noise floor swallows the
signal — and the CI first excludes zero at 20,000 users per arm, the
production-scale spend a large campaign actually reaches. The effect
sweep at 8,000 users shows the same sample is not broken: a 1-point
increment is clearly visible (p < 0.001) where the 0.4-point increment
is not (p = 0.416). The experiment is sized for the effect, and the
ads track's headline increment is too small for the traffic most
campaigns buy. Lewis & Rao (2015, QJE) ran 25 field experiments on
US\$2.8M of digital ad spend and concluded that measuring the returns
to advertising is difficult — this table is the mechanism behind that
result; Blake, Nosko & Tadelis (2015, Econometrica) ran the eBay
search-ads experiment and found the sales loss when ads were switched
off was far smaller than the ad spend, the real-world case where the
increment is near zero.

**A small lift read as a real lift misallocates the next budget.** The
[too-small-to-see detour](when-the-lift-is-too-small-to-see/) computes
the same failure as a confidence interval: at 10,000 users per arm the
half-width is 0.47 points, wider than the 0.4-point increment itself,
so the honest result is "we cannot tell," and 80% power needs 28,547
users per arm. The
[zero-lift detour](when-the-incrementality-is-zero/) is the same
result at its limit: exposed and control both convert at 0.030, a
+0.0% lift, and a report that hides it credits spend with no effect.

**The measurement model decides which channel gets the budget.** The
[overcount detour](when-attribution-overcounts/) shows the
attribution half: three touchpoints share 0.4/0.2/0.4 under
multi-touch, but last-click gives email all 1.0, overcounting by 0.6
and routing next quarter's budget to the wrong channel even when every
ad works. Attribution without a control group is the click-rate
version of the same overcount the stage's increment corrects.

## Who owns the loop

The increment only means something if someone is accountable at each
side of the measurement loop, and each owner is tied to one of the
failure modes above:

- **The experimentation and measurement team** owns the statistical
  contract: power, sample size, the CI, and the SRM gate before the
  outcome is read. It owns the buried-lift failure — the audit
  measured the 0.4-point increment invisible at 8,000 users per arm,
  and shared stage 54's gate catches a broken split at roughly 2,000
  users while the outcome needs 78,000 (Kohavi, Tang & Xu, 2020).
- **The ads platform team** owns the holdout design: which users are
  held out, for how long, and at what ad-load cost — the mission's
  ad-load guardrail held fixed across arms. It owns the
  measurement-vs-settled trade: a bigger holdout sees smaller lifts at
  the price of revenue deferred and users exposed to a worse product.
- **The advertiser and budget owner** owns the spend decision the
  measurement feeds. It owns the misallocation failures — the
  overcount detour's 0.6 of misplaced credit and the zero-lift
  campaign whose report hides the null. A budget decision is only as
  good as the increment it was read from.

When the ownership is implicit, the measurement team ships CIs nobody
sizes, the platform team optimizes the observed click rate, and the
budget follows a lift the experiment cannot see — the audit's 8,000-user
row is that campaign: it spent on a signal that was noise.

## Why this belongs in the mission

This is the ads track's version of the mission's outcome rule — every
capability claim is backed by a measurable outcome. Recommendation has
its offline replay; ads have incrementality. Without the control group,
the ads track would report clicks it never caused, which is the same
failure as a random split leaking the future in [stage
00](../../shared/00-interactions/): the measurement, not the model, decides what
the numbers mean. The audit adds the industrial detail the arithmetic
skips: the control group is not enough — the experiment has to be
sized to see the increment it is trying to measure, and a lift smaller
than the noise floor is the same result as zero.

## Evidence boundary

The executed incrementality split over two declared rates and the
audit's simulated sweeps (fixed seed, binomial noise) are illustrative
and deterministic. They demonstrate the arithmetic and the power
mechanism; real incrementality needs a properly randomized holdout with
the mission's ad-load guardrail held fixed, variance reduction to
shrink the CI, and multiple-testing corrections — the audit's 28,547
per-arm number is the no-variance-reduction baseline. The Lewis & Rao
(2015) and Blake, Nosko & Tadelis (2015) figures are attributed as
published.

## Check your mental model

Answer each before opening it.

**1. Why does the raw click rate overstate the ad's effect, and why
is that not enough to fix?**

<details>
<summary>Answer</summary>

Because some of the exposed users would have converted anyway. The
control group converts at 0.028, so the ad's increment is only the
difference — 0.4 points out of 0.032. Without a control group, the
baseline gets credited to the ad, and spend follows the wrong signal.
But the control group alone is not the fix: at 8,000 users per arm the
audit's CI covers zero, so even with a perfect holdout the campaign
cannot tell the ad worked — the experiment must be sized to the effect
it has to detect.

</details>

**2. A dashboard shows exposed at 0.031 versus control at 0.029, a
0.2-point observed lift. Is the ad working?**

<details>
<summary>Answer</summary>

Not from those numbers. The observed increment is smaller than the
audit's noise floor at campaign scale: the 8,000-user row showed a
0.0000 observed lift and a CI covering zero for a true 0.4-point
effect, and a 0.2-point difference is even harder to see. The CI is
the honest answer — if it covers zero, the campaign is
indistinguishable from noise regardless of the point estimate.

</details>

**3. Why does the measurement model decide which channel gets the
budget?**

<details>
<summary>Answer</summary>

Because the credit, not the campaign, produces the report. Last-click
credits email with 1.0 of a conversion three touchpoints caused,
overcounting by 0.6 against the 0.4/0.2/0.4 multi-touch shares, so
next quarter's budget moves to email even when the ads all worked.
Incrementality experiments are the ground truth that attribution models
are checked against, which is why the measurement owns the decision.

</details>

## Next

The measurement thread continues with interleaving, which swaps the
holdout-sized experiment for a within-user comparison that needs far
less traffic: [interleaving experiments](../38-interleaving-experiments/).

A detour from here: [the campaign's own lift is wider than the interval
that measures it](when-the-lift-is-too-small-to-see/) — the executed CI
read: at 10,000 users per arm the half-width is 0.47 points against a
0.4-point increment, and 80% power needs 28,547 users per arm.

Another detour: [the measurement model decides which channel gets the
budget](when-attribution-overcounts/) — the executed credit read: the
three touchpoints share 0.4/0.2/0.4, but last-click gives email all
1.0, overcounting by 0.6 and misallocating spend.

Another detour: [zero lift is the null result measurement exists to
find](when-the-incrementality-is-zero/) — the executed null read:
exposed and control both convert at 0.030 for a +0.0% lift, so the
campaign changed nothing and a report that hides it credits spend with
no effect.
