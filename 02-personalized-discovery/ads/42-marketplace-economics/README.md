---
status: verified
level: applied
base: scratch
label: Marketplace economics
verified: 2026-08-07
---

# The demand curve sets the peak

**Question:** the ads track priced individual auctions. This stage
steps back and asks how the platform's overall cut behaves and answers:
the take rate trades revenue per transaction against volume, the
revenue curve peaks, and the peak is set by the demand curve — a rate
that is optimal on one market is a collapse on another.

**Before this:** [stage 28 — auction revenue](../28-auction-revenue/)
for the reserve as a revenue decision, and [stage 18 — ad
externality](../18-ad-externality/) for the displacement that ad load
causes.

## The take-rate sweep, executed

The run ([record](runs/2026-08-07-marketplace-economics.md)) sweeps the
take rate on one volume-response curve (`volume = 1000 x (1 - 1.6 x
rate)`):

| rate | volume | revenue |
|---|---:|---:|
| 5% | 920 | \$46 |
| 15% | 760 | \$114 |
| 25% | 600 | \$150 |
| 35% | 440 | \$154 |
| 45% | 280 | \$126 |

## The mechanism, named

Revenue is take rate times volume, and volume falls as the rate rises —
higher costs drive transactions to cheaper alternatives or away
entirely. The product of the two curves peaks: at 35% the executed model
earns \$154, and past it revenue falls even though the per-transaction
cut keeps rising. The platform's cut is not a margin calculation; it is
a marketplace decision about where on the demand curve to sit.

## The failure mode, named and audited

**A fixed take rate is a bet on one demand curve.** The stage's 35%
peak is fitted to one declared volume response. The elasticity audit
([record](runs/2026-08-08-elasticity-sweep.md)) sweeps the slope of the
demand curve — how fast transactions leave when the cut rises — and
measures where the revenue peak sits on each curve:

| elasticity k | peak rate | peak revenue | revenue at 35% | loss vs peak |
|---|---:|---:|---:|---:|
| 1.2 (sticky) | 42.0% | \$208 | \$203 | 2.6% |
| 1.6 (stage) | 31.0% | \$156 | \$154 | 1.4% |
| 2.0 (elastic) | 25.0% | \$125 | \$105 | 16.0% |

The verdict is measured: **THE DEMAND CURVE SETS THE PEAK, AND A RATE
FITTED TO ONE CURVE COSTS REVENUE ON EVERY OTHER.** The stage's fixed
35% is within 2.6 percent of the peak on the curve it was fitted to, but
16.0 percent below the peak on the elastic market; across the two outer
curves the same 35% rate earns \$203 versus \$105 — a 48 percent
revenue difference with no change in the rate. The take rate is a
price, and the demand curve is the marketplace's actual volume
response.

**Raising the cut chases both sides away.** The
[demand-elasticity detour](when-the-demand-curve-is-elastic/) measures
the failure the one-sided curve skips: the side that does not pay still
responds. With the same seller sensitivity, the two-sided revenue peak
falls from 31.0% / \$156.2 to 21.0% / \$92.6, and pricing at the
one-sided optimum earns 15.0 percent below the two-sided peak.

**The take rate can be pushed past the peak into collapse.** The
[take-rate-collapse detour](when-the-take-rate-is-too-high/) reads the
executed sweep past the peak: volume hits zero at 70%, revenue
collapses with it, and the platform's greed is measured in lost
transactions, not gained cuts.

## The fix and its trade

The fix is to estimate the actual volume response before pricing — the
elasticity audit's peak spread is the measurement problem — and to set
the take rate against the measured curve, not a fitted one. The sweep
prices the repair: the stage's fixed 35 percent is within 2.6 percent
of the peak on the curve it was fitted to, but 16.0 percent below the
peak on the elastic market, and across the two outer curves the same 35
percent rate earns \$203 versus \$105 — 48 percent apart with no change
in the rate.

The trade is that the curve moves, and the levers share one elasticity
shape. Estimating elasticity is slow and the answer is only as fresh as
the last experiment; the two-sided response the one-sided curve skips
moves the peak from 31.0 percent to 21.0 percent, and pricing at the
one-sided optimum earns 15.0 percent below the two-sided peak. The
reserve prices demand, the ad load prices displacement, and the take
rate prices the whole market — moving any one lever in isolation
ignores that they sit on the same demand curve, which is the
marketplace team's interaction failure.

## Who owns the loop

The take rate, its demand curve, and the revenue it feeds are owned by
three different teams, and each owner is tied to one of the failure
modes above:

- **The marketplace and pricing team** owns the take rate and the
  elasticity estimate it is set against. It owns the fixed-rate
  failure — a rate fitted to one curve is a bet on one market, and
  the elasticity audit's 42.0% versus 25.0% peak spread is its
  measurement problem, solved by estimating the actual volume
  response before pricing instead of after a revenue drop (Rysman
  2009, "The Economics of Two-Sided Markets", Journal of Economic
  Perspectives 23(3):125-143, doi 10.1257/jep.23.3.125).
- **The two-sided growth team** owns the cross-side response: how the
  side that does not pay reacts to the side that does. It owns the
  feedback failure — the executed two-sided peak of 21.0% against the
  one-sided 31.0% is its blind spot, and it is fixed with matched
  experiments that move one side and measure the other (Rochet and
  Tirole 2003, "Platform Competition in Two-Sided Markets", Journal of
  the European Economic Association 1(4):990-1029).
- **The finance and ads-operations team** owns the revenue the rate
  produces and its interaction with the reserve and ad load. It owns
  the interaction failure — the reserve prices demand, the ad load
  prices displacement, and the take rate prices the whole market, so
  optimizing any one lever in isolation ignores that they share the
  same elasticity shape (Evans 2009, "The Online Advertising Industry:
  Economics, Evolution, and Privacy", Journal of Economic Perspectives
  23(3):37-60).

When the ownership is implicit, the pricing team moves the rate off a
stale curve, the growth team reacts to churn on one side without
measuring the other, and finance reports revenue that neither predicted
— each side correct within its own definition, wrong for the market as
a whole.

## Why this belongs in the mission

The mission began with a value-tree trade and ends with the marketplace
that sets the platform's side of it. Every ads decision — the reserve,
the bid, the ad load — happens under a take rate, and the take rate
decides whether the whole marketplace is healthy. This stage closes the
frontier ads track by making the platform's own economics the measured
object: the peak is not a number, it is a function of the demand curve,
and the two detours price the rate that is too high and the ad load
that displaces too much.

## Evidence boundary

The executed sweep and the elasticity audit run over declared
volume-response models (illustrative, deterministic). They demonstrate
the shape; real take-rate decisions need the actual demand elasticity,
competitor prices, measured volume response, and the cross-side
response, which only a live marketplace provides. The Rysman, Rochet
and Tirole, and Evans citations are attributed as published.

## Check your mental model

Answer each before opening it.

**1. Why does revenue fall after the peak even though the cut keeps
rising?**

<details>
<summary>Answer</summary>

Because volume falls faster than the rate rises. At 45% the platform
takes more per transaction but only 280 transactions remain — revenue
drops from \$154 at 35% to \$126. The take rate is a price, and past
the peak the platform is pricing transactions out of existence.

</details>

**2. Why is 35% optimal in the stage's table but not on every demand
curve?**

<details>
<summary>Answer</summary>

Because the peak is a function of elasticity, not a constant. The
elasticity audit measures peaks of 42.0% on the sticky market and 25.0%
on the elastic one; the stage's 35% loses 2.6 percent of peak revenue
on the curve it was fitted to and 16.0 percent on the elastic curve.
A fixed rate is a bet on one demand curve.

</details>

**3. How is the take rate connected to the reserve and the ad load?**

<details>
<summary>Answer</summary>

All three are the same shape of decision: a platform lever that raises
revenue per unit while shrinking volume, with a peak beyond which the
marketplace loses. The reserve (stage 28) prices demand, the ad load
prices organic displacement, and the take rate prices the whole market.
Optimizing any one in isolation ignores the shared curve — and each
lever also changes what the non-paying side experiences.

</details>

## Next

This closes the frontier ads track (stages 38-42) and with it the
mission's three frontier surfaces: recommendation (31-34), search
(35-37), ads (38-42). Return to [the mission README](../../) for the
full path.

A detour from here: [the demand curve is elastic and the peak
moves](when-the-demand-curve-is-elastic/) — the executed two-sided
read: with the same seller sensitivity the revenue peak falls from
31.0% to 21.0%, and pricing at the one-sided optimum earns 15 percent
below the two-sided peak.

Another detour: [the take rate is too high and the marketplace
collapses](when-the-take-rate-is-too-high/) — the executed sweep read:
revenue peaks around 30-40% and collapses past 70%, so the platform's
greed is measured in lost volume.

Another detour: [the ad load moves and displaces organic
value](when-the-ad-load-moves/) — the executed read: total value peaks
at two ads (\$1.20) and falls after, the same trade as stage 18's
externality set by how many ads a page carries.
