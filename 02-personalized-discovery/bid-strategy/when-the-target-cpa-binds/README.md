---
status: verified
level: applied
base: scratch
label: When the target CPA binds
verified: 2026-08-07
---

# The target CPA is a walk-away line

**Question:** [stage 27's bid strategy](../) derives the bid from value
times conversion. This chapter reads the executed price comparison and
asks when the advertiser should stop bidding.

**Before this:** [stage 27 — bid strategy](../) and its executed
value-per-click model.

## The walk-away, executed

The run ([record](runs/2026-08-07-cpa-binds-read.md)) checks auction
prices against a \$0.10-per-click value:

| auction price | decision |
|---|---:|
| \$0.06 | bid |
| \$0.10 | bid |
| \$0.14 | stand down |
| \$0.20 | stand down |

## The reading

When the auction price passes the click's value, the advertiser stops
bidding — a win at that price is a loss. At \$0.06 and \$0.10 the
advertiser bids; at \$0.14 and \$0.20 it stands down, because the click
is only worth \$0.10. The target CPA is a walk-away line: the bid
protects the budget by refusing the auctions that would break it. The
boundary is exactly the click's expected value — the same number stage
27 derived, now used as a stop price.

## The fix and its trade

The measured fix is to make the walk-away line track the estimate, and
to correct the estimate for what the bidder cannot see. The line is
value times conversion rate, so an inflated conversion estimate raises
it and lets the advertiser overpay — the winner's-log audit shows the
naive read at 0.0316 against a true 0.0188, a 1.68x overbid, and the
delay-corrected labels recover the bid the line should sit on
(Chapelle, 2014, KDD, the joint conversion-and-delay model). The trade
is the line's tightness: a line set from the true value refuses the
overpriced wins but also refuses the auctions where the estimate is
uncertain — the campaign leaves cheap wins on the table while it
learns, which is the same exploration-versus-value tension the cap
detour prices from above. The walk-away line is only as honest as the
estimate that sets it, and the estimate is only as honest as the
sample it was fit on.

## Who owns the loop

- **The bid-strategy team** owns the walk-away line: standing down when
  the auction price passes the click's value, and re-setting the line
  when the estimate moves.
- **The conversion-model team** owns the estimate the line is set on:
  value times conversion rate, corrected for the winner's-log and delay
  biases the stage audit measures.
- **The data and measurement team** owns label maturity per age cohort,
  the input that keeps the conversion estimate — and therefore the
  walk-away line — honest.

## Evidence boundary

The executed price comparison against one declared value (illustrative,
deterministic). It demonstrates the walk-away logic; real bidding
includes competition and multi-auction pacing, but the value boundary
is the same arithmetic.

## Check your mental model

Answer each before opening it.

**1. Why is a win at \$0.14 a loss?**

<details>
<summary>Answer</summary>

Because the advertiser pays per click but values conversions, and each
click is worth \$0.10. Paying \$0.14 for a click that yields \$0.10 of
expected conversion value loses \$0.04 on every win. The auction looks
like a win — the slot was bought — but the economics are negative.

</details>

**2. What is the walk-away line made of?**

<details>
<summary>Answer</summary>

The click's expected value: conversion value times conversion rate.
That number is the bid at the margin and the stop price beyond it. The
line moves when the estimate moves — which is why calibration (stage
16) is the advertiser's problem too: an inflated conversion estimate
raises the walk-away line and lets the advertiser overpay.

</details>

## Next

Back to [stage 27](../), where the bid is the expected value of a
click. The [bid-capped detour](../when-the-bid-is-capped/) shows the
cap's effect on the same decision.
