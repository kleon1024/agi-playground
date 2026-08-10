---
status: verified
level: applied
base: scratch
label: Ad auction
verified: 2026-08-07
---

# Why is revenue per auction collapsing while fill stays flat?

**Question:** an ad competes for a slot through an auction, and the
canonical design is second-price. This stage implements the mechanism,
then audits the operational symptom that shows up in real markets:
impressions are being served, but revenue per auction is falling. The
failure is thin competition — and the fix is not the auction rule.

**Before this:** [stage 06's mixing](../../shared/06-mixing/) for why slots are
scarce, and [stage 05's value tree](../../shared/05-value-tree/) for how an ad's
value is priced.

## The mechanism, executed

The run ([record](runs/2026-08-06-ad-auction.md)) executes the second-price
auction over three scenarios:

| scenario | bids | winner pays |
|---|---:|---:|
| two bidders | [1.00, 0.80] | 0.80 |
| three bidders | [1.20, 1.00, 0.60] | 1.00 |
| one bidder | [0.90] | 0.00 |

Second-price: the highest bidder wins but pays the second-highest bid, so
truthful bidding is dominant and no bidder can game the price by
shading. The one-bidder case shows the boundary: with no competition the
winner pays zero, which is why real auctions add a reserve — and why the
market's bidder depth, not the rule, is what the audit below measures.

<!-- interactive: AdAuction -->

## The failure mode, named and audited

**The market thins, and revenue per auction falls with it.** The audit
([record](runs/2026-08-07-competition-audit.md)) sweeps the number of
bidders per auction over 20,000 auctions per count (fixed seed, values
~ U(0,1), reserve 0.50):

| bidders per auction | revenue per auction | sale rate | share of sales paying the reserve |
|---:|---:|---:|---:|
| 1 | 0.2514 | 50.3% | 100.0% |
| 2 | 0.4140 | 74.7% | 66.9% |
| 4 | 0.6118 | 93.6% | 26.7% |
| 8 | 0.7776 | 99.7% | 3.1% |

The symptom is measured: thinning the market from four bidders to one
cuts revenue per auction by about 59 percent while the sale rate merely
halves — fill looks alive, revenue does not. The reserve-binding share
is the diagnostic: when nearly every sale pays exactly the floor, the
market is thin and the auction has no competition left to set prices.

**The reserve is the fallback, not the fix.** With one bidder the reserve
is the whole auction — every sale pays it. The
[when-the-market-is-thin detour](when-the-market-is-thin/) sweeps the
reserve in a one-bidder market and finds the hump: revenue per auction
peaks at 0.2492 near reserve 0.50, far below the 0.6118 that four
bidders deliver at the same floor. Reserve tuning is the stopgap; bidder
depth is the durable fix, which is why demand-side work (more partners,
an open exchange) and reserve setting are tuned together.

**The reserve set too high kills the sale.** The
[when-the-reserve-price-bites detour](when-the-reserve-price-bites/)
measures the floor's cost side: at reserve 0.85 the second bidder is
eliminated and the winner pays the reserve; a floor above the top bid
leaves the slot unsold. A floor tuned for a deep market, applied to a
thin one, converts auctions into empty slots.

## The fix and its trade

The fix is bidder depth, not the auction rule: the revenue loop earns
when demand-side work — more partners, an open exchange — puts more
bidders in the market, and the competition audit is its instrument. The
measured read is the gap the fix closes: four bidders deliver 0.6118 per
auction where one delivers 0.2514, and the reserve-binding share falls
from 100.0 percent to 3.1 percent as competition returns.

The trade is that depth is slow, and the reserve is the stopgap that pays
while it builds. A floor tuned for a thin market humps at 0.2492 near
reserve 0.50 — far below the 0.6118 four bidders deliver at the same
floor — and a floor set too high converts auctions into empty slots: at
reserve 0.85 the second bidder is eliminated, and a floor above the top
bid leaves the slot unsold. The reserve is part of the auction design,
not an add-on, but the thin-market sweep measures that even a perfectly
tuned reserve cannot replace lost competition.

## Who owns the loop

The auction only earns what someone is accountable for at each side of
the revenue loop, and each owner is tied to one of the failure modes
above:

- **The auction and marketplace-economics team** owns the reserve and the
  auction rule: setting the floor from the demand distribution per slot
  or context, and monitoring the reserve-binding share. It owns the
  kill-the-sale failure mode, and the when-the-market-is-thin sweep is
  its tuning instrument (Vickrey, 1961, *Journal of Finance*; Myerson,
  1981, *Mathematics of Operations Research*: the optimal reserve depends
  on the value distribution, not the bidder count).
- **The supply and demand-acquisition team** owns bidder depth: the
  number of demand partners and the friction of entering the exchange.
  It owns the thin-market failure mode — when the reserve-binding share
  climbs, the fix is on its side, not the auction's (Edelman, Ostrovsky
  and Schwarz, 2007, *American Economic Review* 97(1):242-259; Varian,
  2007, *International Journal of Industrial Organization* 25(6):1163-
  1178: the real position auction's revenue is a property of the
  competing bidders).
- **The ads-measurement team** owns revenue-per-auction monitoring:
  stratifying RPM by bidder count so "fill up, revenue down" is caught
  as a competition failure, not filed as noise. It owns the invisible-
  thinness failure, and the competition audit is its standing check.

When the ownership is implicit, the auction team tunes the reserve
against a demand distribution the supply team never sees, and the
measurement team reports an RPM decline nobody attributes to bidder
churn — the symptom the stage opened with.

## Why this belongs in the mission

Mission 02's contract covers ads as a paid placement inside
recommendation and search. The auction is where the ad's economic value
is revealed — relevance decides pCTR, the bid reveals advertiser value,
and the auction combines them. The audit adds the production loop the
mechanism alone cannot show: the auction's revenue is a property of the
market around it, which is why the stage's owner is the marketplace
team, not the model team.

## Evidence boundary

The executed mechanism over three hand-built bid scenarios and the audit
over synthetic U(0,1) values with a fixed seed are illustrative and
deterministic. They demonstrate the second-price logic and the
competition dependence of revenue; they do not model strategic
multi-round bidding, multi-slot position auctions, or real demand
distributions, where the optimal reserve is estimated from logged bid
data rather than assumed uniform.

## Check your mental model

Answer each before opening it.

**1. Why would an advertiser ever bid their true value?**

<details>
<summary>Answer</summary>

Because second-price makes truth dominant. If you bid below your value,
you only risk losing slots you should have won; if you bid above, you
risk paying more than the item is worth when the second bid is high. The
bid sets your chance of winning; the second bid sets your price. There is
no strategy that improves on bidding your true value, which is why the
mechanism is self-reporting.

</details>

**2. Your RPM fell 30 percent but fill is flat. Where do you look?**

<details>
<summary>Answer</summary>

At bidder depth before the auction rule. The audit measured revenue per
auction falling from 0.6118 (four bidders) to 0.2514 (one bidder) while
the sale rate only halves — fill stays alive while revenue collapses. The
reserve-binding share tells you which regime you are in: when most sales
pay exactly the floor, competition has left the auction and the reserve
is doing all the work. The fix is demand-side, not a rule change.

</details>

**3. What does the one-bidder zero-price case mean for the platform?**

<details>
<summary>Answer</summary>

That with no competition, the second-price auction pays the platform
nothing. That is why real auctions add a reserve price — a minimum the
winner must clear — so a slot is either sold at a floor or not sold at
all. The reserve is part of the auction design, not an add-on, and the
thin-market detour measures that even a perfectly tuned reserve cannot
replace lost competition.

</details>

## Next

Forward to [stage 15 — eCPM ranking](../15-ecpm-ranking/) where the bid
meets the click estimate.

A detour from here: [one bidder makes the reserve the whole auction](when-the-market-is-thin/) — the executed read: revenue per auction humps at 0.2492 near reserve 0.50, while four bidders deliver 0.6118 at the same floor, so depth beats reserve tuning.

Another detour: [the floor that can also kill the sale](when-the-reserve-price-bites/) — the executed reserve sweep read: at 0.85 the second bidder is out and the winner pays the reserve, a real trade between revenue floor and lost sales.

A third detour: [the dominant strategy is the honest one](when-truthful-bidding-is-optimal/) — the executed dominance check read: bidding the true value never yields lower utility than lying, underbidding risks losing and overbidding risks paying more than value.
