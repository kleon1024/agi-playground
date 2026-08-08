---
status: verified
level: applied
base: scratch
label: When truthful bidding is optimal
verified: 2026-08-06
---

# The dominant strategy is the honest one

**Question:** [stage 14's ad auction](../) states that second-price makes
truthful bidding dominant. This chapter reads the executed comparison
across true values and asks where lying could pay.

**Before this:** [stage 14 — ad auction](../) and its executed mechanism.

## The comparison, executed

The run ([record](runs/2026-08-06-truth-read.md)) evaluates bids 0.3,
truthful, and 1.8 against rivals [1.0, 0.8] for three true values:

| true value | bid 0.3 | bid truth | bid 1.8 |
|---:|---|---|---|
| 0.5 | loses, utility 0.00 | loses, utility 0.00 | wins at 1.00, utility -0.50 |
| 1.0 | loses, utility 0.00 | wins at 1.00, utility 0.00 | wins at 1.00, utility 0.00 |
| 1.5 | loses, utility 0.00 | wins at 1.00, utility 0.50 | wins at 1.00, utility 0.50 |

## Two readings

**Lying never improves utility.** Underbidding (0.3) loses every slot,
even the one a truthful 0.5 bid would have won; overbidding (1.8) wins
but can pay more than the slot is worth (true value 0.5, utility -0.50).
The truthful bid reproduces the best of both — the dominance the stage
claimed, now checked rather than asserted.

**Truthfulness is a property of the mechanism, not the advertiser.**
Second-price separates the bid, which sets the chance of winning, from
the price, which is the second-highest bid. An advertiser cannot trade
one against the other, which is why the mechanism is self-reporting: the
platform does not need to know true values to get honest bids.

## The fix and its trade

The fix is the mechanism itself: keep the price decoupled from the bid
so truth is dominant (Vickrey, 1961, *Journal of Finance*). The trade is
revenue: the second-price rule surrenders the winner's surplus — the
platform earns the second bid, not the first. Real search advertising
generalized the rule to position auctions (Edelman, Ostrovsky and
Schwarz, 2007, *American Economic Review* 97(1):242-259; Varian, 2007,
*International Journal of Industrial Organization* 25(6):1163-1178),
where the payment is set by the next ad's bid and truthful bidding is
approximately dominant, and the industry has since moved some markets to
first-price — the transition stage 39 audits. Each rule trades
truthfulness against revenue; the executed utility table is the check
that the truthful bid is the one an advertiser can defend.

## Who owns the loop

- **The auction and marketplace-economics team** owns the payment rule:
  keeping the price decoupled from the bid is the mechanism property
  this detour verifies, and moving a market to first price (stage 39)
  is a rule change the same team owns.
- **The demand-side and bidder-facing team** owns the truthful-bidding
  contract: telling advertisers the bid is their value, and pricing any
  rule change against the utility table this read executes.
- **The ads-measurement team** owns the revenue consequence of the rule,
  comparing the platform's take and the bidder population together,
  never the rule alone.

## Evidence boundary

The executed mechanism over three true values against one fixed rival set
(illustrative, deterministic). It demonstrates dominance inside the
model; real auction analysis also considers reserve prices and
multi-round strategy, which this sweep does not.

## Check your mental model

Answer each before opening it.

**1. Why does overbidding produce negative utility at true value 0.5?**

<details>
<summary>Answer</summary>

Because the bid decides whether you win, but the second-highest bid
decides what you pay. At 1.8 the advertiser wins and pays 1.00 — more
than the 0.5 the slot is worth to them, so the win is a loss. Truthful
bidding avoids exactly this: the bid never rises above the value it is
meant to represent.

</details>

**2. What does the underbid lose that the truthful bid keeps?**

<details>
<summary>Answer</summary>

The chance to win a slot worth more than its price. At true value 0.5,
bidding 0.3 loses to the 1.00 rival, and a profitable 0.5 slot goes
unwon. The truthful bid wins the same slot at 0.80 — positive surplus.
Underbidding protects margin by giving away wins; it never raises
utility above the truthful outcome.

</details>

## Next

Back to [stage 14](../), or to
[the floor that can also kill the sale](../when-the-reserve-price-bites/)
where the one-bidder zero-price case forces the reserve into the design.
