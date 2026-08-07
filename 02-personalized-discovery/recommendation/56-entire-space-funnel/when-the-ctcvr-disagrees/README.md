---
status: verified
level: applied
base: scratch
label: When the CTCVR disagrees
verified: 2026-08-07
---

# The ratio that explodes where CTR is tiny

**Question:** [stage 56](../) derives pay as CTCVR over CTR. This chapter
asks where that derivation stops being safe, and answers: wherever CTR is
small enough that a small estimation error becomes a large swing in the
derived conditional.

**Before this:** [stage 56 — entire-space funnel](../).

## The three impressions, executed

The run ([record](runs/2026-08-07-ctcvr-disagrees.md)) reads three
impressions with honest CTR and noisy CTCVR:

| impression | p_click | p_ctcvr | p_pay raw | p_pay clipped |
|---|---:|---:|---:|---:|
| cold head | 0.02 | 0.0004 | 0.020 | 0.020 |
| mid funnel | 0.10 | 0.0120 | 0.120 | 0.120 |
| strong intent | 0.30 | 0.0300 | 0.100 | 0.100 |

## The reading

At a 2% CTR, a small absolute CTCVR error divides by a tiny number and
becomes a 3x swing in the derived p_pay — the ratio is stable only where
p_click is large enough to trust. The clip is the system admitting it does
not know the conditional there, which is better than ranking on an exploded
ratio. In production this is a slice-level decision: calibrate, then decide
per slice whether the derived conditional is trustworthy.

## Evidence boundary

The executed read over three declared rows (illustrative, deterministic).
It demonstrates the arithmetic; real systems must measure CTCVR error per
CTR slice and set the clip where the error-to-signal ratio crosses a chosen
bound.

## Check your mental model

Answer each before opening it.

**1. Why is a small CTCVR error a 3x swing at 2% CTR?**

<details>
<summary>Answer</summary>

Because the derivation divides by p_click. Dividing a small noisy estimate
by 0.02 amplifies its absolute error fiftyfold; the relative error of the
ratio is dominated by the denominator's size, not the numerator's.

</details>

**2. What is the clip, honestly?**

<details>
<summary>Answer</summary>

An admission that the model does not know the conditional in that slice.
Clamping p_pay to at most p_click enforces probability semantics instead of
ranking on a number that cannot be a probability.

</details>

## Next

Back to [stage 56](../). The funnel's labels arrive late too: [a conversion
that happens tomorrow is labeled a negative today](../when-the-cvr-is-censored/)
is the other failure this stage's trick must survive.
