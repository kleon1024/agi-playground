---
status: verified
level: applied
base: scratch
label: When the bid is capped
verified: 2026-08-07
---

# The cap is a risk dial, not a price

**Question:** [stage 27's bid strategy](../) derives the bid from value.
This chapter reads the executed cap sweep and asks what a bid cap
trades away.

**Before this:** [stage 27 — bid strategy](../) and its executed
value-per-click model.

## The sweep, executed

The run ([record](runs/2026-08-07-bid-capped-read.md)) varies the bid
cap across five auctions:

| cap | wins | total paid |
|---|---:|---:|
| \$0.10 | 3/5 | \$0.30 |
| \$0.08 | 2/5 | \$0.16 |
| \$0.06 | 1/5 | \$0.06 |

## The reading

A tighter cap keeps the advertiser out of expensive auctions but also
out of the cheap ones it could have won at higher bids. The cap is a
risk dial: lower average price, lower reach. Bidding is a budget
decision as much as a value one — the value equation (stage 27) says
what a click is worth, and the cap says how much of the budget the
advertiser is willing to put at risk in pursuit of it.

## The fix and its trade

The measured fix is to set the cap from the win-rate curve, not from
the value equation alone: the cap is a budget-allocation dial, so it
belongs to the campaign's spend target, and the sweep's shape is the
curve it should be tuned on — wins fall 3/5 to 2/5 to 1/5 as the cap
falls \$0.10 to \$0.08 to \$0.06. The trade is the one the table
measures: a tighter cap lowers average price but cuts affordable wins
indiscriminately, and a looser cap buys reach at the risk of
overpaying — which is why the cap must sit under a corrected estimate:
the winner's-log bias alone inflates CVR from 0.0188 to 0.0316 and
would justify a cap 1.68x too high (Chapelle, 2014, KDD, for the
delay-correction side of the estimate; the selection side is the
inverse-propensity weighting of the stage's audit). The cap is the
budget's risk dial, and its position is only as good as the estimate
that sets the value under it.

## Evidence boundary

The executed sweep over five declared auction prices (illustrative,
deterministic). It demonstrates the trade; real bidding also includes
the win-rate curve per auction type, which is how the cap gets set in
production.

## Check your mental model

Answer each before opening it.

**1. Why does a tighter cap lose cheap auctions too?**

<details>
<summary>Answer</summary>

Because the cap applies to the bid, not to the price. A \$0.06 cap
means the advertiser cannot bid \$0.10 even for auctions it would have
won cheaply at that level — the sweep shows wins falling from 3/5 to
1/5. The cap cuts both expensive and affordable wins indiscriminately.

</details>

**2. How is the cap different from the target-CPA walk-away line?**

<details>
<summary>Answer</summary>

The walk-away line refuses auctions where the price exceeds the click's
value; the cap refuses bids above a fixed amount even when the value
justifies them. One protects per-auction economics, the other limits
total risk. Together they bound the bid from two directions: value
below, budget above.

</details>

## Next

Back to [stage 27](../), where the bid is the expected value of a
click. The [target-CPA detour](../when-the-target-cpa-binds/) shows the
value-side bound.
