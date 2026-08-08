---
status: verified
level: applied
base: scratch
label: The calibration break
verified: 2026-08-06
---

# The same strategy, different calibration, different slate

**Question:** [stage 05's value tree](../) collapses predictions into one
scalar. This chapter reads the recorded run and asks what happens to that
scalar when the predictions are miscalibrated.

**Before this:** [stage 05's value tree](../) and its recorded weight sweep.

## The break, read

The run ([record](runs/2026-08-06-break-read.md)) reads the recorded
numbers: with weights unchanged and click predictions inflated 1.6x (not
re-calibrated), the honest and miscalibrated rankings disagree — the top
slots reorder with no product-strategy change.

| ranking | top items |
|---|---|
| honest | item_10, item_11, item_8, item_6, ... |
| miscalibrated | item_11, item_10, item_6, item_2, ... |

## Two readings

**A miscalibrated probability is a different product decision, not a
slightly-wrong number.** The value tree's weights are unchanged; only the
click predictions' scale moved. The slate still reorders, because the
combination arithmetic weights a number that no longer means what the
strategy assumed. That is why stage 04's ECE is a gate: calibration is
what makes "the weights ARE the strategy" a true statement.

**The ad auction is the strategy written as arithmetic.** At trade_rate 0.2
and 0.5 the ad's utility does not clear the organic bar and stays out; at
0.8 it enters and displaces item_6 (organic value 0.499). The explicit
trade rate is the same product decision as the weight sweep — a policy
about how much organic value an ad may displace — made measurable instead
of asserted.

## The fix and its trade

The fix is to re-check calibration before trusting the value arithmetic,
and to treat a slate reorder under fixed weights as a calibration alarm,
not as a strategy change. The executed read prices the failure: with click
predictions inflated 1.6x and every weight untouched, the top slots
reorder — the honest and miscalibrated rankings disagree across the slate,
and the stage's default demo counts 8 of 12 items moving. The value tree
is deterministic; the strategy did not change; only the meaning of the
input number did.

The trade, named: the repair is stage 04's ECE gate plus a re-check when
the training distribution moves, and it costs a held-out set and a
recalibration cadence — the alternative is silently shipping a different
product than the weights declared. The ad auction shows the same failure
in policy form: at trade_rate 0.2 and 0.5 the ad's utility does not clear
the organic bar, and at 0.8 it enters and displaces item_6 (organic value
0.499) — a miscalibrated organic score changes which items an ad is
allowed to displace, which is a revenue decision wearing an arithmetic
error.

## Who owns the loop

- **The model team** owns the calibration gate that prevents the break —
  the ECE number is the shipping bar for every prediction the tree
  consumes.
- **The evaluation team** owns the slate-reorder read as the break
  detector: fixed weights, moving slate, and a calibration audit fires.
- **The ads and monetization team** owns the trade-rate and displacement
  read, and re-validates it whenever the organic scoring changes.

## Evidence boundary

The recorded weight sweep and auction (12 and 30-item synthetic catalogues,
seed 42). It reads those artifacts; it does not re-run the tree and the
reordering characterizes the synthetic item set.

## Check your mental model

Answer each before opening it.

**1. Why does a 1.6x inflation reorder the slate if the weights are
unchanged?**

<details>
<summary>Answer</summary>

Because combination arithmetic is sensitive to scale, not just to rank. The
weights encode a strategy over calibrated probabilities; a 1.6x inflation
changes each item's click contribution relative to its satisfaction
contribution, so the weighted sums reorder even though no weight moved. The
strategy is a claim about what the numbers mean, and miscalibration breaks
that claim.

</details>

**2. What is the auction's trade rate actually deciding?**

<details>
<summary>Answer</summary>

How much organic value an ad may displace. At 0.2 and 0.5 the ad's utility
is below the organic bar and the slate keeps the organic item; at 0.8 the
ad clears the bar and displaces item_6. The trade rate is the product
policy — how aggressively to monetize — written as a number, and the
recorded threshold (0.8) is where this synthetic catalogue flips.

</details>

## Next

Back to [stage 05](../), or to
[the weight IS the strategy](../when-the-weight-moves/) which reads the same
run's weight sweep.
