---
status: verified
level: applied
base: scratch
label: Ad auction
verified: 2026-08-06
---

# The winner pays the second bid

**Question:** when an ad competes for a slot, the allocation is an
auction, not a ranking. This stage implements the canonical second-price
mechanism and asks why it is the design the industry converged on.

**Before this:** [stage 06's mixing](../06-mixing/) for why slots are
scarce, and [stage 05's value tree](../05-value-tree/) for how an ad's
value is priced.

## The mechanism, executed

The run ([record](runs/2026-08-06-ad-auction.md)) executes the second-price
auction over three scenarios:

| scenario | bids | winner pays |
|---|---:|---:|
| two bidders | [1.00, 0.80] | 0.80 |
| three bidders | [1.20, 1.00, 0.60] | 1.00 |
| one bidder | [0.90] | 0.00 |

## The mechanism, named

Second-price: the highest bidder wins the slot but pays the
second-highest bid. Three properties fall out:

1. **Truthful bidding is dominant** — bid your true value, because your
   bid sets your chance of winning while the second bid sets your price.
2. **No bidder can game the price** — lowering your bid only lowers your
   chance of winning, not what you would pay if you won.
3. **Efficiency** — the item goes to the bidder who values it most.

The one-bidder case shows the boundary: with no competition the winner
pays zero, which is why real auctions add a reserve price (the platform's
minimum) — a mechanism stage 15's eCPM ranking interacts with.

## Why this belongs in the mission

Mission 02's contract covers ads as a paid placement inside
recommendation and search. The auction is where the ad's economic value is
revealed — and it is the reason the value tree cannot simply rank ads by
relevance: relevance decides pCTR, the bid reveals advertiser value, and
the auction combines them.

## Evidence boundary

The executed mechanism over three hand-built bid scenarios (illustrative,
deterministic). It demonstrates the second-price logic; it does not model
strategic multi-round bidding or reserve-price optimization, which real
auction design studies.

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

**2. What does the one-bidder zero-price case mean for the platform?**

<details>
<summary>Answer</summary>

That with no competition, the second-price auction pays the platform
nothing. That is why real auctions add a reserve price — a minimum the
winner must clear — so a slot is either sold at a floor or not sold at
all. The reserve is part of the auction design, not an add-on, and it is
where the platform's revenue floor lives.

</details>

## Next

Forward to [stage 15 — eCPM ranking](../15-ecpm-ranking/) where the bid
meets the click estimate.

A detour from here: [the floor that can also kill the sale](when-the-reserve-price-bites/) — the executed reserve sweep read: at 0.85 the second bidder is out and the winner pays the reserve, a real trade between revenue floor and lost sales.
