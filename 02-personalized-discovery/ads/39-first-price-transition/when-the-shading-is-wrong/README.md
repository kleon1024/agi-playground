---
status: verified
level: applied
base: scratch
label: When the shading is wrong
verified: 2026-08-07
---

# The shading is wrong and the error is a direct cost

**Question:** [stage 39's first-price bidder](../) shades its bid. This
chapter reads the executed error sweep and asks what a wrong shading
estimate costs.

**Before this:** [stage 39 — first-price transition](../) and its
executed shading model.

## The error, executed

The run ([record](runs/2026-08-07-shading-is-wrong-read.md)) compares
three bids against a unit value:

| strategy | bid | win | net |
|---|---:|---:|---:|
| under-shade | \$0.80 | 0.80 | \$0.16 |
| optimal | \$0.50 | 0.50 | \$0.25 |
| over-shade | \$0.20 | 0.20 | \$0.16 |

## The reading

Under-shading wins more but pays too much; over-shading keeps more
margin but loses auctions. Both lose to the optimum — \$0.16 against
\$0.25 — so the shading estimate's error is a direct cost, not a
second-order effect. The two errors are symmetric around the peak: 30%
too high and 60% too low cost the same. First-price bidding is an
estimation problem: the bidder must guess the competition, and the
guess's error is measured in lost net value.

## The fix and its trade

The fix is to treat the shading estimate as a distribution, not a
point. The bidder does not know the competitor distribution; it knows
an estimate of it, and the executed sweep prices the point-estimate
error. The robust move is to bid the optimum of the *expected*
distribution over the belief's uncertainty, or to add a margin on the
side where error costs more — a brand advertiser who needs reach
shades less (losing the win is the expensive failure), a margin-tight
bidder shades more (overpaying is the expensive failure). The trade is
that robustness gives up the peak: the point-estimate optimum's \$0.25
is only available to a bidder whose belief is exactly right, and any
hedge moves the operating point down the curve the sweep measured —
\$0.16 on both sides of the peak in this model. The other half of the
fix is buying signal, which the
[competition-unobservable detour](../when-the-competition-is-unobservable/)
prices: probing win rates is the only way the estimate's uncertainty
shrinks, and probing spends margin.

## Who owns the loop

- **The demand-side bidding team** owns the shading estimate as a
  distribution, not a point: bidding the optimum over the belief's
  uncertainty, and hedging toward the side where error costs more.
- **The measurement and forecasting team** owns the error-cost read —
  the \$0.16-versus-\$0.25 sweep is its acceptance number for shading
  quality.
- **The auction and pricing team** owns the transition context the
  estimate lives in: first price made the bid the price, which is why
  the estimate's error lands directly in net value.

## Evidence boundary

The executed sweep over a declared value and win model (illustrative,
deterministic, uniform competitor). It demonstrates the mechanism; real
shading needs the actual competitor distribution, which is
unobservable, so the estimate's error distribution has to be modeled —
which is exactly what the fix-and-trade above does with the sweep's own
numbers.

## Check your mental model

Answer each before opening it.

**1. Why is under-shading expensive even though it wins more?**

<details>
<summary>Answer</summary>

Because the bid is the price. Under-shading at \$0.80 wins 80% of
auctions, but every win pays \$0.80 against a value of \$1.00 — net
\$0.16 per auction. The higher win rate cannot compensate for the
thinner margin, so the bidder loses 36% of the optimum's value. In
first price, winning more and keeping less is still losing.

</details>

**2. What makes this an estimation problem rather than a pricing
rule?**

<details>
<summary>Answer</summary>

Because the optimal bid depends on the competition, which the bidder
cannot see. The \$0.50 optimum falls out of a uniform competitor
model; a different distribution gives a different optimum. The bidder
must estimate that distribution from past auctions, and the estimate's
error lands directly in net value — exactly what the executed sweep
shows. The bid is a prediction, not a rule.

</details>

## Next

Back to [stage 39](../). The
[market-adjustment detour](../when-the-market-adjusts/) shows the
aggregate side: as every bidder learns to shade, platform revenue
falls.
