---
status: verified
level: applied
base: scratch
label: When the label arrives late
verified: 2026-08-07
---

# The label that arrives late biases the training set

**Question:** [stage 44's skew](../) is about features that change. This
chapter asks about labels that arrive late — conversions logged hours
after the click — and answers: a training cut taken now only sees the
labels that arrived early.

**Before this:** [stage 44 — training-serving consistency](../) and its
executed skew read.

## The early-only cut, executed

The run ([record](runs/2026-08-07-label-arrives-late-read.md)) cuts the
training set at hour 6. P1001's conversions arrived within the window;
P1002's and P1003's arrive later:

| item | clicks | total conversions | visible at cut | estimate (true) |
|---|---:|---:|---:|---:|
| P1001 | 500 | 20 | 20 | 0.0400 (0.0400) |
| P1002 | 400 | 12 | 0 | 0.0000 (0.0300) |
| P1003 | 300 | 9 | 0 | 0.0000 (0.0300) |

## The reading

P1002 and P1003 converted slowly, so the cut at hour 6 sees zero of their
labels and estimates 0.0000 — half their true rate. The model trains on
the fast-converting items only. The label arrival delay is a sampling
bias: the training set does not represent the traffic, it represents the
traffic that answered quickly. The fix is to hold out the unconfirmed
window and train on fully-labelled data, not to trust a cut that is
really a filter.

## Evidence boundary

The executed cut over three declared items (illustrative, deterministic).
It demonstrates the mechanism; real pipelines must measure the label
arrival distribution, choose the holdout window against it, and watch for
the same bias in any online metric computed on partial labels.

## Check your mental model

Answer each before opening it.

**1. Why does P1002 estimate 0.0000 when its true rate is 0.0300?**

<details>
<summary>Answer</summary>

Because none of its 12 conversions arrived before the hour-6 cut. The
estimate is computed from what is visible, and nothing is visible. The
model therefore believes P1002 converts never, and ranks it below items
that are actually worse — the bias is in the timing of the label, not in
the click.

</details>

**2. How is a late label different from a missing feature (stage 43)?**

<details>
<summary>Answer</summary>

A missing feature is absent at serve time; a late label is absent at
training time. Both look like bookkeeping and both silently decide the
rank. The difference is the fix: the store makes the feature default
explicit, while the late label needs a holdout window so the model never
trains on a partially-observed target.

</details>

## Next

Back to [stage 44](../). The [online-feature-lag
detour](../when-the-online-feature-lags/) is the other side of the same
skew: the serving value, not the label, moving after the snapshot.
