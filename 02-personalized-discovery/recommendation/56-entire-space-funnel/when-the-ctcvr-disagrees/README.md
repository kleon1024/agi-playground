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

## The fix and its trade

The fix is a two-step read per CTR slice: calibrate the CTCVR head, then
set the clip where the error-to-signal ratio crosses a chosen bound. The
three-row read shows the arithmetic: at a 2% CTR the honest p_pay is
0.020, and a small absolute CTCVR error divides by 0.02 to become a 3x
swing — so the slice-level clip is what keeps the derived conditional a
probability instead of a ranked noise number.

The trade, named: clipping is an admission that the model does not know
the conditional in that slice, which means the system deliberately stops
ranking there. That is better than ranking on an exploded ratio, but it
is a real decision — the clip hides the small-CTR slice from the
downstream value estimate, and the slice is often exactly where a
long-tail item lives. The decision is per slice, not global, which is why
it cannot be one constant set once at launch.

## Who owns the loop

- **The model team** owns the per-slice CTCVR error measurement and the
  clip bound: it has to be derived from the measured error-to-signal
  curve, not guessed.
- **The serving team** owns the clip as a served decision — the derived
  conditional that leaves the score path must already be clipped, because
  downstream stages multiply whatever they receive.
- **The evaluation team** owns the calibration check per CTR slice and
  the re-check when the funnel changes (a new page, a new intent class —
  the small-CTR regime moves).

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
