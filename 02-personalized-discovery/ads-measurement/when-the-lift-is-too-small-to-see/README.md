---
status: verified
level: applied
base: scratch
label: When the lift is too small to see
verified: 2026-08-08
---

# The campaign's own lift is wider than the interval that measures it

**Question:** [stage 30's ads measurement](../) measures the ad by its
0.4-point increment. This chapter reads the executed confidence-interval
audit and asks why that increment is so hard to see in practice.

**Before this:** [stage 30 — ads measurement](../) and its executed
lift-power audit, and [shared stage 54](../../../shared/54-online-experiments/)
for the experiment gate the mission already built.

## The CI, executed

The run ([record](runs/2026-08-08-lift-ci.md)) computes the 95 percent
confidence interval for the 0.4-point increment at four sample sizes
(fixed seed), plus the per-arm sample size a proper experiment needs:

| n per arm | CI half-width | the interval covers zero? |
|---:|---:|---|
| 1,000 | 1.42 points | yes |
| 10,000 | 0.47 points | yes |
| 100,000 | 0.15 points | no |
| 1,000,000 | 0.05 points | no |

Sample size for 80% power: 28,547 users per arm (90% power: 38,216).

## The failure mode, named

**The interval is wider than the effect it measures.** At 10,000 users
per arm the half-width is 0.47 points while the entire increment is
0.4 points — the experiment cannot distinguish the ad's effect from
zero, and the honest result is "we cannot tell." The CI only excludes
zero at roughly 100,000 users per arm, which is production-scale spend
for one experiment. Lewis & Rao (2015, QJE) ran 25 field experiments on
US\$2.8M of digital ad spend and concluded that measuring the returns
to advertising is difficult: this CI table is the mechanism behind that
conclusion. The fix is not a better model — it is sizing: the
experiment is designed for the effect it must detect, and a 0.4-point
increment needs 28,547 users per arm before the test has power. Shared
stage 54's gate makes the same point from the other side: SRM is
detectable at roughly 2,000 users while a 2 percent outcome effect
needs about 78,000, which is why the split is checked before the
outcome is read.

**The same sample sees big effects fine.** At 10,000 users per arm a
1-point increment is clearly visible (half-width 0.49 points, p <
0.001). The measurement is not broken; it is calibrated to effects of
its own size. A campaign whose increment is smaller than the CI cannot
be evaluated by that experiment, whatever the observed lift says — and
that is the statistical form of the [zero-lift detour](../when-the-incrementality-is-zero/):
an observed lift inside a wide interval is the same result as a null.

## The fix and its trade

The fix is to size the experiment to the increment before spending: a
power calculation up front (the 28,547-user number is that
calculation), a larger or longer holdout, or a cheaper proxy metric
that moves enough to be measured (clicks and reach have tighter CIs
than conversions, at the price of measuring the wrong outcome). Shared
stage 54's SRM gate then runs before the outcome is read, because the
split check needs a fraction of the traffic. The trade is that power is
expensive: an experiment big enough to see 0.4 points excludes a lot of
users from the ad for a long time, and the alternative — run the
campaign unmeasured and trust the observed lift — is exactly the
failure the [overcount detour](../when-attribution-overcounts/) names:
the report credits the ad with the baseline. Small-increment campaigns
need a cheaper decision surface, not a smaller experiment.

## Who owns the loop

- **The experimentation and measurement team** owns the power
  calculation: an experiment is sized to the increment it must detect
  (28,547 users per arm for 0.4 points at 80 percent power), and the CI
  is reported with it.
- **The ads platform team** owns the holdout cost — bigger experiments
  exclude users from the ad — and the cheaper proxy metrics that trade
  outcome fidelity for measurable movement.
- **The shared experiment gate (stage 54)** owns the SRM check that runs
  before the outcome is read, since the split fails at a fraction of
  the traffic the effect needs.

## Evidence boundary

The executed CI audit uses the normal approximation to the binomial
difference over declared rates (fixed seed). It demonstrates the
sizing mechanism; real power calculations also include variance
reduction (CUPED, stratification) and multiple-testing corrections,
which lower the required n at the price of added assumptions. The
US\$2.8M and 25-experiment figures are Lewis & Rao (2015, QJE),
attributed as published.

## Check your mental model

Answer each before opening it.

**1. Why is a 0.4-point observed lift not evidence the ad worked at
10,000 users per arm?**

<details>
<summary>Answer</summary>

Because the CI half-width (0.47 points) is wider than the increment
itself. The interval covers zero, so the data cannot distinguish the
effect from binomial noise — the honest reading is "we cannot tell,"
and the observed 0.4 points is consistent with both 0 and the true
effect.

</details>

**2. Why check for SRM before reading the outcome?**

<details>
<summary>Answer</summary>

Because the split fails first. Shared stage 54's SRM check fires at
roughly 2,000 users while a 2 percent outcome effect needs about 78,000
for power — the sample-ratio check is 39 times cheaper. If the split
drifted, every outcome number is comparing the wrong populations, so
the gate runs on a fraction of the traffic and the outcome is read only
after it passes.

</details>

## Next

The next measurement step is interleaving, which swaps the
holdout-sized experiment for a within-user comparison that needs far
less traffic: [interleaving experiments](../../38-interleaving-experiments/).
