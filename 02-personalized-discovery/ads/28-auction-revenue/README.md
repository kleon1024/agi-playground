---
status: verified
level: applied
base: scratch
label: Auction revenue
verified: 2026-08-07
---

# The auction rule is a revenue decision

**Question:** [stage 14's second-price auction](../14-ad-auction/)
revealed value. This stage asks what the payment rule does to revenue,
and answers: the same bids pay different amounts under first- and
second-price — and bidder behavior under the rule is the other half of
the equation.

**Before this:** [stage 14 — ad auction](../14-ad-auction/) for the
auction mechanism, and [stage 27 — bid strategy](../27-bid-strategy/)
for where the bids come from.

## The rules, executed

The run ([record](runs/2026-08-07-auction-revenue.md)) executes the
same bids `[1.20, 1.00, 0.80]` under both payment rules:

| rule | winner pays |
|---|---:|
| first price | \$1.20 |
| second price | \$1.00 |
| gap | \$0.20 |

## The mechanism, named

First price pays the winner's own bid; second price pays the
second-highest. The identical bids pay the platform 20 cents more per
auction under first price — but that gap is not free revenue:
advertisers know the rule and shade their bids, which is why the
honest-bidding property of stage 14 matters. Revenue per auction is
only half the question; bidder behavior under the rule is the other
half, and the [shading detour](when-first-price-pays-more/) executes
both.

## Why this belongs in the mission

The mission's contract prices ads by revenue minus displacement. The
auction rule decides the revenue side, so choosing the rule is a
product decision with a measurable revenue shape — including the
reserve, which the [reserve detour](when-the-reserve-moves-revenue/)
shows has its own optimum on the demand curve.

## Evidence boundary

The executed payment comparison over one bid set (illustrative,
deterministic, no strategic iteration). It demonstrates the mechanism;
real revenue comparisons also need the bidder population's behavior
under each rule, which is exactly the coupling the shading detour
measures.

## Check your mental model

Answer each before opening it.

**1. Why is the 20-cent gap not free revenue?**

<details>
<summary>Answer</summary>

Because bidders anticipate the rule. Under first price the winner pays
its own bid, so rational bidders shade below value; the shading detour
shows the gap shrink from \$0.20 to \$0.16 once bidders shade. The rule
and the bidder population are coupled — the revenue comparison is only
valid for the bidding behavior it assumes.

</details>

**2. What does the reserve do to the curve?**

<details>
<summary>Answer</summary>

It trades fill against price. A zero reserve fills every slot at zero
price; a high reserve prices each sale high but sells few. The
revenue-maximizing reserve sits between the two — \$0.37 at a \$0.8
reserve in the executed sweep — and is a property of the demand curve,
which is why it is estimated, not guessed.

</details>

## Next

Forward to [stage 29 — RTB pipeline](../29-rtb-pipeline/) where the
auction must run inside a 100ms deadline.

A detour from here: [first price pays more only when bidders stay
honest](when-first-price-pays-more/) — the executed shading read: naive
bidders pay \$1.20 under first price versus \$1.00 under second, but
shaded bidders narrow the gap to \$0.16, so the revenue comparison
assumes the bidding behavior.

Another detour: [the reserve sits on the demand
curve](when-the-reserve-moves-revenue/) — the executed sweep read:
expected revenue peaks at \$0.37 around a \$0.8 reserve, then falls as
fill collapses, so the reserve is estimated from the demand curve, not
guessed.
