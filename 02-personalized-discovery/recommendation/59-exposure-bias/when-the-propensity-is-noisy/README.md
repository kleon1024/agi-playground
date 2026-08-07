---
status: verified
level: applied
base: scratch
label: When the propensity is noisy
verified: 2026-08-07
---

# The weight that turns a few rows into the whole fit

**Question:** [stage 59](../) reweights logged rows by inverse exposure
propensity. This chapter asks what happens when the propensity model is
noisy, and answers: the inverse of a noisy small propensity is a huge
weight, so a handful of rows steer the fit — until the weight is capped.

**Before this:** [stage 59 — exposure bias](../).

## The variance, executed

The run ([record](runs/2026-08-07-propensity-noisy.md)) compares exact
propensities, noisy ones, and noisy ones with a weight cap:

| propensity source | mean w | max w | quality rank corr |
|---|---:|---:|---:|
| exact | 1.5 | 4.1 | 0.980 |
| noisy | 216.6 | 10,000.0 | 0.376 |
| noisy + cap 20 | 2.6 | 20.0 | 0.986 |

## The reading

A small propensity with a little noise becomes a weight in the thousands,
so a few rows dominate the loss and the correlation collapses to 0.376.
Capping the weight trades a little unbiasedness for a lot of variance and
recovers the correlation to 0.986 — better than the exact propensities.
In production the propensity model is itself logged and audited, because
the correction is only as trustworthy as the estimate it divides by.

## Evidence boundary

The executed read over a synthetic exposure log (illustrative,
deterministic). It demonstrates the variance mechanism; real systems must
measure the propensity error per slice and set the cap where the
variance-bias trade is worth it.

## Check your mental model

Answer each before opening it.

**1. Why does a little propensity noise explode the weights?**

<details>
<summary>Answer</summary>

Because IPS divides by the propensity. A 2% propensity with noise can read
as 0.02% or 2%, and the inverse swings from 50 to 5,000 — the variance of
the ratio is dominated by the small-denominator rows.

</details>

**2. What does capping the weight cost?**

<details>
<summary>Answer</summary>

A little unbiasedness: capped rows are not weighted by their true inverse
propensity. In exchange it removes the variance that let a few rows steer
the fit, which is the cheaper failure in practice.

</details>

## Next

Back to [stage 59](../). Why exploration is worth real money: [2%
exploration reaches under 200 of 2,000 catalogue items](../when-exploration-traffic-is-thin/).
