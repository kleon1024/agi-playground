---
status: verified
level: applied
base: scratch
label: LTV and CAC
verified: 2026-08-07
---

# A user is worth what they keep returning and spending

**Question:** stage 54 followed the advertiser's return. This stage asks
the same question for the platform's own users, and answers: lifetime
value is retention times revenue per retained user, acquisition cost is
what a channel charges for a signup, and the ratio decides which channels
the platform can afford to buy users from at all.

**Before this:** [stage 30 — ads measurement](../../ads/30-ads-measurement/) for
the attribution these numbers depend on, and [stage 54 — advertiser
ROAS](../../ads/54-advertiser-roas/) for the advertiser-side economics this
completes.

## The unit economics, executed

The run ([record](runs/2026-08-07-ltv-and-cac.md)) computes the five-month
lifetime value per user for two channels:

| channel | cac | ltv | ltv/cac |
|---|---:|---:|---:|
| organic search | \$2.00 | \$12.15 | 6.08 |
| paid installs | \$8.00 | \$7.50 | 0.94 |

## The mechanism, named

Organic search pays back about six times its acquisition cost; paid
installs return less than the cost of the user — every paid signup loses
money once retention is counted. A channel with a low CAC is not a cheap
channel if its users leave. Lifetime value is retention times revenue per
retained user summed over the horizon, and acquisition cost is what the
channel charges; unit economics decide which growth is real growth.

## Why this belongs in the mission

The mission ends where the platform's health is decided: a discovery
system that improves retention changes LTV, and LTV is what makes every
acquisition channel affordable. The ads track priced impressions; this
stage prices users, closing the loop the mission opened with "reduce the
time to find something worth attention" — because time saved is retention
earned, and retention is the multiplier in the unit economics.

## Evidence boundary

The executed five-month LTV over declared retention and revenue
(illustrative, deterministic). It demonstrates the mechanism; real unit
economics need the measured retention curve per cohort, real revenue per
user, the attribution window, and channel CACs — all of which shift and
must be re-measured.

## Check your mental model

Answer each before opening it.

**1. Why does paid installs lose money despite paying for signups?**

<details>
<summary>Answer</summary>

Because the signup is only the start of the ledger: paid installs cost
\$8.00 and return \$7.50 over five months — the user's revenue does not
cover the acquisition. The channel is not cheap at the install; it is
expensive in the retention, because its users leave before paying back
their cost.

</details>

**2. What does an LTV/CAC ratio below 1 mean for growth?**

<details>
<summary>Answer</summary>

That every user bought through the channel is a loss: scaling the channel
scales the loss, so "growth" through it is actually shrinking the
company. The ratio is the gate that separates real growth — channels
where LTV clears CAC — from vanity volume, and it is why the retention
work (the flattening-cohort detour) is worth more than any single
acquisition push.

</details>

## Next

The unit economics close the mission's loop: retention is what discovery
earns. A detour from here: [the user who costs more than they return is
a liability at any volume](when-cac-exceeds-ltv/) — the executed read:
referral clears its cost at 3.06, paid installs lose money at 0.94.

Another detour: [the user who stops leaving is worth more than the user
who stops coming](when-retention-flattens/) — the executed read: a 35%
retention floor nearly doubles 24-month LTV from \$27.54 to \$50.83.
