---
status: verified
level: applied
base: scratch
label: Advertiser ROAS
verified: 2026-08-07
---

# The advertiser's return is the platform's revenue

**Question:** stages 14-30 priced the auction. This stage steps back to
the advertiser who pays for it, and answers: the platform earns what
advertisers spend, and an advertiser keeps spending only while return on
ad spend clears their target — so the marginal dollar's decay is the
lifecycle that makes advertiser retention a platform concern.

**Before this:** [stage 27 — bid strategy](../27-bid-strategy/) for the
target-CPA walk-away line, and [stage 30 — ads
measurement](../30-ads-measurement/) for the incrementality that decides
the return.

## The lifecycle, executed

The run ([record](runs/2026-08-07-advertiser-roas.md)) tracks one
advertiser's weekly spend at a fixed average order value:

| week | spend | conversions | revenue | roas |
|---|---:|---:|---:|---:|
| 1 | \$1,000 | 310 | \$8,680 | 8.68 |
| 2 | \$1,000 | 325 | \$9,100 | 9.10 |
| 3 | \$1,000 | 265 | \$7,420 | 7.42 |
| 4 | \$1,000 | 165 | \$4,620 | 4.62 |

## The mechanism, named

ROAS falls from a strong start to 4.62, below the target of 5.0. The
advertiser does not leave at a plateau; they leave when the marginal
dollar stops paying. The platform that watches only its own revenue is
watching the advertiser walk away: as the campaign matures, the audience
that was already inclined is exhausted, conversions decay, and ROAS
approaches the walk-away line — which is where the platform's revenue
stops, too.

## Why this belongs in the mission

The ads track (14-30) priced slots as if demand were fixed. This stage
opens the demand side: the advertiser's budget is the platform's revenue
line, and the auction's price is only half the story. Every earlier
decision — the eCPM ranking, the pacing, the measurement — exists to keep
the advertiser's return above their exit line, so ROAS is not an
advertiser metric; it is the platform's churn metric.

## Evidence boundary

The executed weekly lifecycle over a declared AOV (illustrative,
deterministic). It demonstrates the mechanism; real advertiser economics
need the measured conversion decay per cohort, the real AOV, and the
advertiser's actual target — which the platform only sees through bids
and churn.

## Check your mental model

Answer each before opening it.

**1. Why does ROAS fall while spend stays flat?**

<details>
<summary>Answer</summary>

Because the same spend reaches progressively colder audiences: week 1
bought 310 conversions from the already-inclined, week 4 only 165 from
whoever is left. Revenue falls with conversions, so ROAS decays even
though the advertiser changed nothing. The campaign's decline is not an
auction failure — it is the audience exhausting itself.

</details>

**2. What is the walk-away line, and who sets it?**

<details>
<summary>Answer</summary>

The ROAS (or CPA) below which the advertiser stops spending. The line is
the advertiser's, set by their own economics; the platform can only see
it when the budget moves. The platform's job is to slow the decay — via
relevance, placement, and measurement — because once the line is crossed,
the auction cannot bid the advertiser back (the budget-moves detour).

</details>

## Next

The advertiser's return decays; stage 55 prices the user lifecycle that
feeds it. A detour from here: [the marginal dollar buys less every
time](when-roas-collapses/) — the executed read: CPA climbs from \$3.23
to \$6.59 as spend doubles, and ROAS falls below the \$5 target.

Another detour: [the advertiser's exit is the platform's loss](when-the-budget-moves/)
— the executed read: when a rival channel returns 4.6x and the platform
3.1x, the budget moves and platform revenue falls by half.
