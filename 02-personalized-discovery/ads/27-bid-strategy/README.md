---
status: verified
level: applied
base: scratch
label: Bid strategy
verified: 2026-08-07
---

# The bid is an expected value, not a guess

**Question:** [stage 14's auction](../14-ad-auction/) decides the price
once bids exist. This stage asks where a bid comes from, and answers:
the advertiser bids the expected value of a click — value times
conversion rate.

**Before this:** [stage 14 — ad auction](../14-ad-auction/) for the
mechanism bids enter, and [stage 16 — CTR calibration](../16-ctr-calibration/)
for the estimate the bid inherits.

## The bid, executed

The run ([record](runs/2026-08-07-bid-strategy.md)) derives the bid
from declared advertiser inputs:

| input | value |
|---|---:|
| target CPA | \$5 |
| conversion rate | 2% |
| value per click | \$0.10 |
| target CPA bid | \$0.10 |

## The mechanism, named

A target-CPA bid is value times conversion rate. The advertiser values
a conversion at \$5, expects 2% of clicks to convert, so each click is
worth \$0.10 — and that is the bid. Two properties fall out:

1. **The bid changes with the estimate.** If the conversion rate is
   wrong, the bid is wrong, which is why calibration (stage 16) is the
   advertiser's problem too.
2. **The bid is a walk-away line.** When the auction price passes the
   click's value, the advertiser stops bidding — the
   [target-CPA detour](when-the-target-cpa-binds/) executes that
   refusal.

## Why this belongs in the mission

The mission's ads track ran the platform's side of the auction. This
stage completes the loop by deriving the advertiser's side: the bid is
the value signal the auction needs. It also closes back to the mission's
contract — the platform and the advertiser are two parties with
non-identical interests, and the bid is where those interests meet.

## Evidence boundary

The executed derivation from declared inputs (illustrative,
deterministic). It demonstrates the mechanism; real bidding also
includes competition, budget constraints, and the bidder's own
uncertainty, which the [bid-capped detour](when-the-bid-is-capped/)
prices.

## Check your mental model

Answer each before opening it.

**1. Why does the bid depend on the conversion estimate?**

<details>
<summary>Answer</summary>

Because the advertiser pays per click but values conversions. A click
is worth value times conversion rate, so an error in the conversion
estimate is an error in the bid. That is why calibration is shared:
the platform's pCTR and the advertiser's CVR both feed the same
economic decision.

</details>

**2. What happens when the auction price passes the bid?**

<details>
<summary>Answer</summary>

The advertiser stops bidding — a win at that price is a loss. The
target CPA is a walk-away line: at \$0.14 against a \$0.10 click value
the advertiser stands down, protecting the budget by refusing the
auctions that would break it.

</details>

## Next

Forward to [stage 28 — auction revenue](../28-auction-revenue/) where
the payment rule, not just the bids, moves the money.

A detour from here: [the target CPA is a walk-away
line](when-the-target-cpa-binds/) — the executed refusal read: against
a \$0.10/click value the advertiser bids at \$0.06 and \$0.10 and
stands down at \$0.14 and \$0.20, because a win at that price is a
loss.

Another detour: [the cap is a risk dial, not a
price](when-the-bid-is-capped/) — the executed sweep read: lowering the
cap from \$0.10 to \$0.06 drops wins from 3/5 to 1/5 and spend from
\$0.30 to \$0.06, trading reach for lower average price.
