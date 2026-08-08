---
status: verified
level: applied
base: scratch
label: When the market is thin
verified: 2026-08-07
---

# One bidder makes the reserve the whole auction

**Question:** [stage 14's audit](../) showed revenue per auction falls as
bidders disappear. This chapter reads the executed one-bidder reserve
sweep and asks what the platform can still do when the market is thin.

**Before this:** [stage 14 — ad auction](../) and its competition audit.

## The sweep, executed

The run ([record](runs/2026-08-07-thin-market.md)) sweeps the reserve in a
one-bidder market (value ~ U(0,1), 50,000 draws per reserve):

| reserve | revenue per auction | sale rate |
|---:|---:|---:|
| 0.00 | 0.0000 | 1.0000 |
| 0.30 | 0.2097 | 0.6989 |
| 0.50 | 0.2492 | 0.4985 |
| 0.60 | 0.2404 | 0.4006 |
| 0.90 | 0.0894 | 0.0993 |

## Two readings

**Revenue per auction humps at the monopoly reserve.** With one bidder the
reserve is both the price and the filter: at 0.00 every auction sells for
nothing, at 0.90 almost nothing sells. The peak near 0.50 (0.2492) is
where the price and the sale probability balance — the reserve that a
revenue-maximizing seller sets when it faces a single buyer, the
monopoly reserve (Myerson, 1981, *Mathematics of Operations Research*).
Setting the floor is not a constant; it is a curve the demand
distribution decides.

**Thinness is a market failure, not a reserve failure.** The stage audit
measured four bidders at reserve 0.50 earning 0.6118 per auction — more
than double the best any reserve can do with one bidder. No reserve
setting recovers the lost competition, which is why the fix for a thin
market is bidder depth (more demand partners, opening the exchange),
with the reserve as the fallback while depth is missing.

## The fix and its trade

The measurable fix has two parts. The reserve is set from the demand
distribution per slot or per context, not as a global constant: sweep it
against expected revenue exactly as this read does, and take the hump's
peak (Vickrey, 1961, *Journal of Finance*: reserve prices are part of
the mechanism; Myerson, 1981: the optimal reserve depends only on the
value distribution). The other part is demand-side: recruit bidders
until the reserve-binding share falls — in the stage audit the share of
sales paying the floor drops from 100 percent (one bidder) to 3.1
percent (eight). The trade is on the second part: more demand partners
means more supply, integration, and fee negotiation, which is why the
fallback reserve exists at all.

## Who owns the loop

- **The auction and marketplace-economics team** owns the reserve as the
  fallback: setting the floor from the demand distribution per slot or
  context, and monitoring the reserve-binding share — the thin-market
  alarm this detour's sweep instruments.
- **The supply and demand-acquisition team** owns bidder depth, the
  durable fix the 0.25-vs-0.61 comparison prices: recruiting demand
  partners and lowering the friction of entering the exchange is its
  job, and the reserve only holds while depth is missing.
- **The ads-measurement team** owns competition-stratified RPM:
  reporting revenue per auction by bidder count so thinness is caught
  as a market failure, not filed as noise.

## Evidence boundary

The executed sweep (values drawn from U(0,1), fixed seed, 50,000 draws
per reserve — illustrative, deterministic). It demonstrates the hump and
the fallback role of the reserve; it does not model strategic bidders,
multi-slot auctions, or real demand distributions, where the optimal
reserve is estimated from logged bid data, not assumed uniform.

## Check your mental model

Answer each before opening it.

**1. Why does revenue per auction fall on both sides of reserve 0.50?**

<details>
<summary>Answer</summary>

Because the reserve is two instruments at once. Below the peak, raising
the floor raises the price on sales that still happen faster than it
loses marginal sales. Above the peak, the floor starts excluding the
cheap half of the value distribution, and lost sales cost more than the
higher price earns. The hump is the point where the two effects
balance.

</details>

**2. Your market thinned from four bidders to one. Where do you look
first?**

<details>
<summary>Answer</summary>

At bidder depth, not the reserve. The measured numbers say the reserve's
best case with one bidder (0.25) is less than half of four bidders'
revenue (0.61). Re-tune the reserve as a stopgap, but the durable fix is
bringing bidders back — more demand partners, better audience match,
lower friction to enter the exchange. The reserve-binding share is the
monitor: when nearly every sale pays the floor, the market is thin.

</details>

## Next

Back to [stage 14 — ad auction](../), or to
[stage 15 — eCPM ranking](../../15-ecpm-ranking/) where the bid meets the
click estimate.
