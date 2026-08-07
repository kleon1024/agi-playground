---
status: verified
level: applied
base: scratch
label: When the market adjusts
verified: 2026-08-07
---

# The market adjusts as bidders learn to shade

**Question:** [stage 39's first-price transition](../) changed the
bidder's strategy. This chapter reads the executed learning curve and
asks what happens to platform revenue as bidders adapt.

**Before this:** [stage 39 — first-price transition](../) and its
executed shading model.

## The adjustment, executed

The run ([record](runs/2026-08-07-market-adjusts-read.md)) reads revenue
as bidders learn to shade:

| phase | shading | revenue per auction |
|---|---:|---:|
| naive | 1.00 | \$0.95 |
| transition | 0.70 | \$0.68 |
| settled | 0.50 | \$0.42 |

## The reading

As bidders learn to shade, the platform's revenue per auction falls —
the first-price transition moved revenue from the platform to the
advertisers over time. Naive bidders overpay; trained bidders shade
toward the optimum, and each step of learning costs the platform
revenue. A revenue forecast that assumes naive bidding overstates the
steady state: the first-price rule looks good on launch day and decays
as the demand side learns.

## Evidence boundary

The executed learning curve over three declared phases (illustrative,
deterministic, assumed shading evolution). It demonstrates the
mechanism; real transition revenue needs the actual bidder population
and its learning speed, which a live market would show.

## Check your mental model

Answer each before opening it.

**1. Why did the transition's early revenue overstate the steady
state?**

<details>
<summary>Answer</summary>

Because bidders had not learned yet. At the transition, advertisers
still bid near full value, so the platform collected \$0.95 per auction
— the naive phase. As they learned the first-price shading optimum,
revenue fell to \$0.42. The launch-day number was the transient, not
the equilibrium, and a forecast built on it priced the market at its
most naive moment.

</details>

**2. Where did the revenue go, and is that the transition's point?**

<details>
<summary>Answer</summary>

It went to the advertisers — the same value, reallocated. The
transition moved the surplus from the platform to the demand side as
bidders stopped overpaying. Whether that is good depends on the
platform's goal: lower advertiser cost attracts demand, but the revenue
line falls. The measured shape — naive to settled — is what a market
decision has to price before switching rules.

</details>

## Next

Back to [stage 39](../). The
[wrong-shading detour](../when-the-shading-is-wrong/) shows the
individual bidder's side of the same learning: the error cost of a bad
shade estimate.
