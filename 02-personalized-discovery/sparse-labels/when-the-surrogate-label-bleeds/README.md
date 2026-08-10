---
status: verified
level: applied
base: scratch
label: When the surrogate label bleeds
verified: 2026-08-07
---

# The surrogate fills the empty slice and inflates every probability

**Question:** [stage 65's surrogate variant](../) uses "engaged" as a
stand-in for purchase. This chapter measures the price: a model trained on
the surrogate learns the surrogate's rate, so its predicted purchase
probability is inflated and its true-label AUC is worse.

**Before this:** [stage 65 — sparse labels](../) and [stage 05 — the value
tree](../../../shared/05-value-tree/), which multiplies every predicted
probability into money decisions. This detour is the surrogate's price
tag.

## The bleed, executed

The run ([record](runs/2026-08-07-surrogate-bleed-read.md)) trains a
true-label model and a surrogate-trained model on the same cold rows:

| model | true-label buy AUC |
|---|---:|
| true labels | 0.756 |
| surrogate labels | 0.706 |

Surrogate mean predicted buy rate on cold items: 0.0395. True buy rate on
cold items: 0.0036.

## The reading

The surrogate fills the empty slice — engaged is several times more
frequent than purchase, so the model trained on it produces usable ranking
(0.706 true-label AUC). But it reads "engaged" everywhere and over-predicts
purchase by about 11x (0.0395 predicted against 0.0036 true), and on the
labels that matter its true-label AUC is the worse of the two. A surrogate
buys signal and sells probability meaning: the inflated number propagates
into the value tree, which multiplies it into every downstream decision.
The published route for the same shape in delayed feedback is a weighting
and a calibration repair, not the label alone — Ktena et al. (RecSys
2019) and Yasui et al. (arXiv:2002.02068, CIKM 2020) both correct the
label's rate before the model's probability is trusted.

## The fix and its trade

The failure is the surrogate's hidden price: it fills the empty slice
and over-predicts purchase by about 11x — 0.0395 predicted against 0.0036
true on cold items — and on the labels that matter its true-label AUC
(0.706) is worse than the true-label model's (0.756). The fix is not the
label alone; it is the published correction pair — re-weight and
re-calibrate the surrogate's rate before the probability is trusted
(Ktena et al., RecSys 2019; Yasui et al., CIKM 2020). The trade is
measured by the same run: the surrogate buys usable ranking on an
otherwise empty slice (0.706 is far above chance) and sells probability
meaning — the inflated number propagates into the value tree, which
multiplies it into every downstream decision, so the calibration repair
is part of the fix, not an option.

## Who owns the loop

- **The sample and label team** owns the surrogate hierarchy and its
  rate: the gap between engaged and purchase is this team's number, and
  the density report carries it.
- **The model team** owns the correction: re-weighting and calibration
  before the surrogate's probability ships.
- **The product and downstream owner** owns the multiplied decision: the
  value tree feeds every probability into money decisions, so a
  surrogate that ships uncorrected leaks the inflation everywhere.

When ownership is implicit, the surrogate ships because its ranking
"looks usable," and the 11x inflation surfaces in the first downstream
money decision.

## Evidence boundary

The executed synthetic read over one cohort with a declared engaged rate
(illustrative, deterministic, single seed). It demonstrates the inflation
mechanism and its magnitude; real systems must measure the surrogate's
rate gap and the resulting probability inflation on production traffic
before the surrogate ships.

## Check your mental model

Answer each before opening it.

**1. Why does the surrogate inflate the purchase rate so much?**

<details>
<summary>Answer</summary>

Because the model fits the label it sees. Engaged is several times more
frequent than purchase, so a model trained on engaged learns a rate near
the engaged rate and emits it where purchase is being predicted. The
executed read shows 0.0395 predicted against 0.0036 true — about 11x.

</details>

**2. Can a surrogate be used without paying the inflation?**

<details>
<summary>Answer</summary>

Not by the label alone. The published fixes re-weight and re-calibrate
the surrogate's rate before the probability is trusted (Ktena et al.,
RecSys 2019; Yasui et al., CIKM 2020), and even then the ranking may
carry the surrogate's noise. The value tree multiplies the number, so
the calibration repair is part of the fix, not an option.

</details>

## Next

Back to [stage 65](../), where the surrogate is one of the three fix
layers — now with its price measured.
