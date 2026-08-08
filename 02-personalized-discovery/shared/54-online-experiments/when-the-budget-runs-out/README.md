---
status: verified
level: applied
base: scratch
label: When the budget runs out
verified: 2026-08-08
---

# How many users does the A/B need, and which lever moves the date?

**Question:** [stage 54's gate](../) reads a finished experiment, but the
two questions every shipping team asks before one starts are "how many
users" and "how long". This chapter answers both with a calculator, not a
guess: it derives the 39,244-users-per-arm figure
[the split-lies detour](../when-the-split-lies/) asserted, then sweeps the
four levers that change it — minimum detectable effect, metric variance,
CUPED variance reduction, and traffic allocation plus controlled rollout —
and prices each one in calendar days.

**Before this:** [when the split lies](../when-the-split-lies/) for the
39,244/78,489 figure this chapter derives, and [stage 54's gate](../) for
the validity conditions the design has to satisfy before the read starts.

## The budget, executed

The run ([record](runs/2026-08-08-budget.md)) computes sample size from the
standard normal formula — n per arm = 2(z_alpha/2 + z_beta)^2 / delta^2,
the same formula and z constants the split-lies detour used — and converts
the result to days at 10,000 eligible users per day. The baseline: detect a
2% effect at 80% power, two-sided alpha 5%.

**The number, derived.** At delta = 0.02 the formula returns 39,244 users
per arm and 78,489 total, matching the split-lies detour to the user. The
detail the split-lies detour skipped: the "2%" is a standardized effect —
2% of the outcome's standard deviation, not of its mean. At a 4% CTR,
delta 0.02 is a 0.39 percentage-point lift; at a 10% baseline it is 0.60
points. Sample size is written in variance units, which is why the metric
itself is a design lever.

**Lever 1 — the minimum detectable effect.** Halving the effect quadruples
the sample, because the formula is quadratic in delta:

| MDE (SD units) | users/arm | total | days at 10k/day |
|---|---:|---:|---:|
| 0.01 | 156,978 | 313,955 | 31.4 |
| 0.02 | 39,244 | 78,489 | 7.8 |
| 0.05 | 6,279 | 12,558 | 1.3 |
| 0.10 | 1,570 | 3,140 | 0.3 |

The same quadratic shape bites the other direction: power 90% instead of
80% costs 52,537 users per arm, 34% more. The power curve at delta 0.02 is
a hockey stick — 20,000 users per arm buys only 52% power, so a test cut
short for the calendar misses a real 2% effect about half the time.

**Lever 2 — metric variance.** For a proportion metric the variance is
p(1-p), so the same absolute lift needs very different samples depending on
the baseline:

| baseline p | sigma | users/arm | relative |
|---|---:|---:|---:|
| 0.01 | 0.0995 | 6,216 | 1.0x |
| 0.10 | 0.3000 | 56,512 | 9.1x |
| 0.50 | 0.5000 | 156,978 | 25.3x |

The noisy 50% metric needs 25x the users of the 1% metric for the same 0.5
point lift. Choosing a less noisy metric — or a proxy with lower variance —
is a free lever only if the proxy still tracks the decision.

**Lever 3 — CUPED.** A pre-experiment covariate with correlation rho cuts
the sample by the factor (1 - rho^2), because it removes the share of
outcome variance the covariate explains (Deng, Xu, Kohavi and Walker,
2013, WSDM):

| rho | factor | users/arm | days at 10k/day |
|---|---:|---:|---:|
| 0.0 | 1.000 | 39,244 | 7.8 |
| 0.5 | 0.750 | 29,433 | 5.9 |
| 0.7 | 0.510 | 20,015 | 4.0 |
| 0.9 | 0.190 | 7,456 | 1.5 |

At rho 0.9 the same experiment finishes in 1.5 days instead of 7.8 — the
single biggest legitimate accelerator on this list, because it works on
the variance the formula is written in.

**Lever 4 — allocation and ramp.** The variance of the difference is
sigma^2(1/n1 + 1/n2), so at a fixed total, 50/50 minimizes it, and any
skew inflates the total users for the same power:

| control share | variance ratio | total users |
|---|---:|---:|
| 0.5 | 1.000 | 78,489 |
| 0.7 | 1.190 | 93,439 |
| 0.8 | 1.563 | 122,639 |
| 0.9 | 2.778 | 218,024 |

And the calendar: 78,489 users at 10,000/day is 7.8 days, at 2,000/day it
is 39 days, at 500/day it is 157 days — the experiment that "cannot finish
this quarter" is usually a throughput statement. A controlled rollout
(Xia, Bhardwaj, Dmitriev and Fabijan, 2019, ICSE-SEIP) adds time even at
fixed users: a linear 0-to-100% ramp over 14 days turns the 7.8-day
experiment into a 14.8-day one, and a 28-day ramp into 21 days. Safety and
finish-date trade directly in the ramp length.

## The reading

Sample size is a budget equation in three terms — the variance of the
metric, the effect you must detect, and the power you insist on — and the
calendar is the budget divided by throughput. The four levers are not
equal: MDE and CUPED change the numerator, allocation changes the
denominator's efficiency, and the ramp changes how fast users accumulate.
The design verdict is a sentence, not a feeling: "the honest MDE at fixed
power needs N users; throughput delivers that in D days; the window is W,
so either reduce variance, widen the MDE with the business, or run a
cheaper design." Peeking early is not a fifth lever — it is what
underpowered reading looks like (Kohavi, Tang and Xu, 2020; Zhou, Lu and
Shallah, 2023, arXiv:2305.16459).

## The fix and its trade

The fix is to size before you launch and to name which lever pays for the
date. The trade is that every accelerator costs something: raising the MDE
means the experiment may miss the effect you actually shipped; CUPED needs
a covariate measured before the experiment and only pays when rho is high;
skewing the split preserves power only by adding total users; and the ramp
— the only lever that never helps the date — is kept because it is the
safety mechanism for the change itself. The unglamorous part of the fix is
organizational: the MDE belongs to the business, the metric variance to
the analysis team's metric choice, and the ramp length to the platform's
release policy, so the sizing conversation is a handoff between three
owners before the experiment exists.

## Who owns the loop

- **The product or business owner** sets the MDE: the smallest effect that
  is worth shipping. This is the input the whole budget hangs on, and
  changing it is the cheapest way to move the date.
- **The analysis team** owns the metric's variance — which metric, which
  baseline, whether a CUPED covariate exists and how well it correlates —
  because the sample size formula is written in variance units.
- **The experimentation platform team** owns allocation and rollout: the
  declared split, the ramp policy, and the throughput assumption that
  converts users to days.

## Evidence boundary

The run is a deterministic calculator over one fixed scenario (10,000
eligible users per day, 2% standardized effect), not a real experiment's
outcome. It verifies the sample-size arithmetic and prices the tradeoffs;
the CUPED factor and rollout costs rest on the cited external results
(Deng et al., 2013; Xia et al., 2019), and real variance reduction depends
on covariates the scenario does not model. The numbers are the cost of the
design, not evidence about the change being tested.

## Check your mental model

**1. Why does halving the MDE quadruple the sample?**

<details>
<summary>Answer</summary>

Because the sample-size formula is quadratic in the effect: n is
proportional to 1/delta^2. Detecting an effect half as large needs four
times the users, and the days follow the users.

</details>

**2. A teammate proposes 80/20 traffic to protect the control. What do
you say?**

<details>
<summary>Answer</summary>

Unequal splits inflate total users for the same power: the variance of the
difference is sigma^2(1/n1 + 1/n2), minimized at 50/50, and 80/20 costs
56% more users — 122,639 instead of 78,489 in the baseline scenario. If
the goal is to limit exposure, the ramp, not the split, is the mechanism.

</details>

**3. The experiment cannot finish this quarter. What are the legitimate
options, in order?**

<details>
<summary>Answer</summary>

Reduce variance first (CUPED, or a less noisy metric), then widen the MDE
with the business if the smaller effect is genuinely not worth shipping,
then consider a cheaper design. Peeking early is not an option: it changes
the false-positive rate the fixed-horizon test was sized for.

</details>

## Next

The budget assumes the split is clean; the validity gate and its detours
police that assumption once the experiment runs. From here:
[when the traffic is two-sided](../when-the-traffic-is-two-sided/) — the
switchback where the block unit prices a 1% effect at 36 years, the
extreme case of the allocation lever; and back to
[stage 54's gate](../) for the checks that decide whether the result is
readable.
