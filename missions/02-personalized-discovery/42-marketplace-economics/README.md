---
status: verified
level: applied
base: scratch
label: Marketplace economics
verified: 2026-08-07
---

# The take rate is a marketplace decision

**Question:** the ads track priced individual auctions. This stage steps
back and asks how the platform's overall cut behaves and answers: the
take rate trades revenue per transaction against volume, and the
revenue curve peaks — beyond it, the marketplace loses both.

**Before this:** [stage 28 — auction revenue](../28-auction-revenue/)
for the reserve as a revenue decision, and [stage 18 — ad
externality](../18-ad-externality/) for the displacement that ad load
causes.

## The take-rate sweep, executed

The run ([record](runs/2026-08-07-marketplace-economics.md)) sweeps the
take rate:

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

## Why this belongs in the mission

The mission began with a value-tree trade and ends with the marketplace
that sets the platform's side of it. Every ads decision — the reserve,
the bid, the ad load — happens under a take rate, and the take rate
decides whether the whole marketplace is healthy. This stage closes the
frontier ads track by making the platform's own economics the measured
object, with the two detours pricing the rate that is too high and the
ad load that displaces too much.

## Evidence boundary

The executed sweep over a declared volume-response model (illustrative,
deterministic). It demonstrates the shape; real take-rate decisions need
the actual demand elasticity, competitor prices, and measured volume
response, which only a live marketplace provides.

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

**2. How is the take rate connected to the reserve and the ad load?**

<details>
<summary>Answer</summary>

All three are the same shape of decision: a platform lever that raises
revenue per unit while shrinking volume, with a peak beyond which the
marketplace loses. The reserve (stage 28) prices demand, the ad load
prices organic displacement, and the take rate prices the whole market.
Optimizing any one in isolation ignores the shared curve.

</details>

## Next

This closes the frontier ads track (stages 38-42) and with it the
mission's three frontier surfaces: recommendation (31-34), search
(35-37), ads (38-42). Return to [the mission README](../) for the full
path.

A detour from here: [the take rate is too high and the marketplace
collapses](when-the-take-rate-is-too-high/) — the executed sweep read:
revenue peaks around 30-40% and collapses past 70%, so the platform's
greed is measured in lost volume.

Another detour: [the ad load moves and displaces organic
value](when-the-ad-load-moves/) — the executed read: total value peaks
at two ads (\$1.20) and falls after, the same trade as stage 18's
externality set by how many ads a page carries.
