---
status: verified
level: applied
base: scratch
label: When ROAS collapses
verified: 2026-08-07
---

# The marginal dollar buys less every time

**Question:** [stage 54's lifecycle](../) decays week over week. This
chapter asks what scaling does to the return, and answers: the extra
dollar reaches a colder audience every time — CPA climbs with spend, and
the walk-away line is a spend level.

**Before this:** [stage 54 — advertiser ROAS](../) and its executed
weekly lifecycle read.

## The scale-up, executed

The run ([record](runs/2026-08-07-roas-collapses-read.md)) raises the
advertiser's weekly spend across three levels at a fixed AOV and CPA
target:

| spend | conversions | cpa | roas |
|---|---:|---:|---:|
| \$1,000 | 310 | \$3.23 | 8.68 |
| \$2,000 | 430 | \$4.65 | 6.02 |
| \$3,000 | 455 | \$6.59 | 4.25 |

## The reading

Doubling the budget buys only 120 more conversions; the third thousand
buys 25. CPA climbs from \$3.23 to \$6.59 and ROAS falls below the \$5
target. The marginal dollar is the whole story of scaling — the average
return hides that the next dollar loses money. The advertiser's "average"
ROAS looks fine at \$3,000 of spend; the decision that matters is the
return on the last dollar, which is already below the line.

## Evidence boundary

The executed scale-up over declared conversion decay (illustrative,
deterministic). It demonstrates the mechanism; real budget decisions need
the measured conversion curve per audience segment, not the average, and
the advertiser's marginal target.

## Check your mental model

Answer each before opening it.

**1. Why does the third thousand buy only 25 conversions?**

<details>
<summary>Answer</summary>

Because the audience is ordered by inclination: the first dollars reach
people already ready to buy, and each further dollar reaches someone
colder. The marginal conversion count falls 120, then 25, so the marginal
CPA climbs steeply. The campaign is not breaking — it is exhausting the
ready audience, which is a law of the audience, not a failure of the
auction.

</details>

**2. Why is the marginal return the number that matters?**

<details>
<summary>Answer</summary>

Because the advertiser scales at the margin: the next dollar is accepted
or refused on what it will return, not on what the campaign averaged.
Here the average ROAS at \$3,000 is 4.25 — above the headline — while the
last dollar is already below the \$5 target. The platform that reports
averages is describing a decision the advertiser makes on the margin,
and the two diverge exactly where the advertiser walks away.

</details>

## Next

Back to [stage 54](../). The [budget-moves detour](../when-the-budget-moves/)
is what happens next: the advertiser reallocates by measured ROAS, and
the platform's revenue falls with the share.
