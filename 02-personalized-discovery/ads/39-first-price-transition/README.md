---
status: verified
level: applied
base: scratch
label: First-price transition
verified: 2026-08-07
---

# In first price, the bid is the price

**Question:** stage 14's auction was second-price, where the winner
pays the second bid. This stage asks what changes when the winner pays
its own bid and answers: bidding becomes shading — the bidder must
discount its true value, because the bid sets both the win probability
and the price.

**Before this:** [stage 14 — ad auction](../14-ad-auction/) for
second-price truthfulness, and [stage 28 — auction
revenue](../28-auction-revenue/) for the rule change that moved the
industry from second to first price.

## The shading sweep, executed

The run ([record](runs/2026-08-07-first-price-transition.md)) sweeps
the bid factor against a unit value:

| factor | bid | win | net |
|---|---:|---:|---:|
| 1.00 | \$1.00 | 1.00 | \$0.00 |
| 0.80 | \$0.80 | 0.80 | \$0.16 |
| 0.60 | \$0.60 | 0.60 | \$0.24 |
| 0.50 | \$0.50 | 0.50 | \$0.25 |
| 0.40 | \$0.40 | 0.40 | \$0.24 |

## The mechanism, named

In first price the winner pays its own bid, so net is (value - bid)
times win probability. Bid the full value and any win nets zero; shade
too much and wins disappear. With a uniform competitor the optimum is
half the value: bidding \$0.50 nets \$0.25, the peak of the executed
curve. The bid is now an estimation problem — the bidder has to guess
the competition to know how much to shade.

## Why this belongs in the mission

The ad market's transition from second to first price changed the
bidder's core decision: truthfulness stopped being optimal, and the
whole demand side had to relearn bidding. That is a marketplace
mechanism change, exactly the kind of thing this mission exists to
quantify — stage 28 compared the rules, this stage prices the
transition's cost to bidders and the market-adjustment detour shows
its cost to the platform over time.

## Evidence boundary

The executed sweep over a declared value and win model (illustrative,
deterministic, uniform competitor). It demonstrates the mechanism; real
bidding needs the actual competitor distribution, which is
unobservable, so shading is estimated — the shading-error detour prices
that estimation risk.

## Check your mental model

Answer each before opening it.

**1. Why is bidding the full value a losing strategy in first price?**

<details>
<summary>Answer</summary>

Because the bid is the price. A win at the full value pays everything
the impression is worth to the bidder — net is exactly zero, and a
second-price bidder used to winning at the second price now pays its
own bid. The executed run shows it directly: bidding \$1.00 wins
everything and nets \$0.00.

</details>

**2. Why is the optimum half the value here?**

<details>
<summary>Answer</summary>

Because with a uniform competitor, shading to half the value balances
the two losses. Under-shading wins more but pays too much; over-shading
keeps more margin but loses auctions. The product (value - bid) times
win probability peaks at the halfway bid — \$0.50 nets \$0.25, above
both \$0.80's \$0.16 and \$0.40's \$0.24.

</details>

## Next

The frontier ads track continues. Next is [stage 40 — privacy-safe
attribution](../40-privacy-safe-attribution/), where measurement
survives differential privacy.

A detour from here: [the shading is wrong and the error is a
direct cost](when-the-shading-is-wrong/) — the executed read:
under-shading at \$0.80 wins more but nets \$0.16, over-shading at
\$0.20 loses auctions, and both lose to the \$0.50 optimum's \$0.25.

Another detour: [the market adjusts as bidders learn to
shade](when-the-market-adjusts/) — the executed read: platform revenue
per auction falls from \$0.95 under naive bidding to \$0.42 once
bidders shade, so a forecast that assumes naive bidding overstates the
steady state.
