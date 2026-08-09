---
status: verified
level: applied
base: scratch
label: Advertiser ROAS
verified: 2026-08-07
---

# The average hides the margin

**Question:** stages 14-30 priced the auction. This stage steps back to
the advertiser who pays for it, and answers: the platform earns what
advertisers spend, an advertiser keeps spending only while return on ad
spend clears their target — and the return that matters is the marginal
dollar's, which the average report hides.

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
dollar stops paying. As the campaign matures, the audience that was
already inclined is exhausted, conversions decay, and ROAS approaches
the walk-away line — which is where the platform's revenue stops, too.
The platform that watches only its own revenue is watching the
advertiser walk away.

## The failure mode, named and audited

**The campaign looks on target while the next dollar already loses.**
The average ROAS report mixes dollars that behave differently, so it
can clear the target at every spend level while the marginal dollar is
below it. The marginal audit ([record](runs/2026-08-08-marginal-roas.md))
splits the spend into \$500 increments and measures both returns:

| spend | conversions | average ROAS | marginal ROAS (over last increment) |
|---|---:|---:|---:|
| \$1,000 | 310 | 8.68 | - |
| \$1,500 | 403 | 7.52 | 5.21 |
| \$2,000 | 473 | 6.62 | 3.92 |
| \$2,500 | 523 | 5.86 | 2.80 |
| \$3,000 | 558 | 5.21 | 1.96 |

The verdict is measured: **THE AVERAGE HIDES THE MARGIN — THE REPORT
SAYS 5.21X WHILE THE NEXT DOLLAR RETURNS 1.96X.** Average ROAS stays
above the 5.0 target from \$1,000 to \$3,000, while marginal ROAS
clears the target only on the first increment (5.21) and falls to 1.96
on the last. A budget decided on the average keeps spending \$1,500 on
dollars that return below the target; a budget decided on the margin
stops at \$1,500. The two rules disagree by exactly the dollars that
are hardest to defend.

**The marginal dollar decays as the campaign scales.** The
[ROAS-collapse detour](when-roas-collapses/) measures the decay itself:
as spend doubles, CPA climbs from \$3.23 to \$6.59 and ROAS falls below
the target — the average return hides that the next dollar loses money,
which is why the walk-away line is a spend level, not a number.

**The advertiser reallocates on the measured number, and the platform
loses with the share.** The [budget-moves
detour](when-the-budget-moves/) is the consequence: when the measured
return says a rival channel wins, the budget moves and platform revenue
falls by half, and the auction cannot bid the advertiser back once the
measurement says leave.

## The fix and its trade

The fix is to decide the budget at the margin: scale and cut against
marginal ROAS, not the campaign average, because the average mixes
dollars that behave differently. The audit prices the repair — average
ROAS stays above the 5.0 target from \$1,000 to \$3,000 while marginal
ROAS clears the target only on the first increment (5.21) and falls to
1.96 on the last, so a budget cut from the top loses \$980 per \$500
where the same cut from the first increment loses \$2,604.

The trade is that the marginal number is the expensive one to produce.
It requires the incrementality experiments stage 30 owns — which Lewis
& Rao (2015) warn are hard, and Blake, Nosko & Tadelis (2015) show can
find near-zero effects — so the average report is what finance ships
and the media buyer decides against, a number that is confidently wrong.
The consequence is the budget-moves detour: when the measured return
says a rival channel wins, the budget moves and platform revenue falls
by half, and the auction cannot bid the advertiser back once the
measurement says leave.

## Who owns the loop

The budget, its measurement, and the number the budget is decided
against are owned by three different teams, and each owner is tied to
one of the failure modes above:

- **The advertiser's media buyer** owns the budget and the cut
  decisions, made at the margin. It owns the marginal-vs-average
  failure — the executed gap between the 5.21 average and the 1.96
  marginal dollar is its decision error, fixed by scaling and cutting
  against the marginal target instead of the campaign report (Google
  Ads, "Optimize for marginal ROI instead of average ROI",
  support.google.com/google-ads/answer/12850633, consulted 2026-08-08).
- **The platform's measurement team** owns the incrementality
  experiments that produce the real return. It owns the
  misattribution failure — the eBay field experiment found sales
  barely moved when paid search ads were cut, so the attributed
  average over-credited the ads (Blake, Nosko, and Tadelis 2015,
  "Consumer Heterogeneity and Paid Search Effectiveness: A Large-Scale
  Field Experiment", Econometrica 83(1):155-174, doi 10.3982/ECTA12423)
  — and stage 30's discipline is its fix.
- **Finance and ads-operations** owns the reported number the budget
  is decided against. It owns the reporting failure — a report that
  shows the average without the margin gives the media buyer a number
  that is confidently wrong, and Lewis and Rao (2015, "The Unfavorable
  Economics of Measuring the Returns to Advertising", Quarterly Journal
  of Economics 130(4):1941-1973, doi 10.1093/qje/qjv023) are the
  warning that the right number is expensive to produce.

When the ownership is implicit, the media buyer scales on the average,
the measurement team produces attribution instead of incrementality,
and finance reports a return that hides the dollar that already loses —
each side correct within its own definition, wrong for the budget as a
whole.

## Why this belongs in the mission

The ads track (14-30) priced slots as if demand were fixed. This stage
opens the demand side: the advertiser's budget is the platform's revenue
line, and the auction's price is only half the story. Every earlier
decision — the eCPM ranking, the pacing, the measurement — exists to keep
the advertiser's return above their exit line, so ROAS is not an
advertiser metric; it is the platform's churn metric. The frontier
failure is that the return is measured as an average, and the average
deceives both sides of the budget: it keeps the advertiser spending on
losing dollars and hides from the platform which revenue is about to
leave.

## Evidence boundary

The executed lifecycle and the marginal audit run over declared
conversion curves (illustrative, deterministic, fixed \$28 AOV). They
demonstrate the mechanism; real advertiser economics need the measured
conversion decay per cohort, the real AOV, the advertiser's actual
target, and the marginal curve — which only the incrementality
measurement stage 30 owns can produce. The Blake, Nosko and Tadelis,
Lewis and Rao, and Google Ads citations are attributed as published or
as consulted on the date shown.

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

**2. Why can the average ROAS clear the target while the marginal
dollar loses?**

<details>
<summary>Answer</summary>

Because the average mixes the early dollars that return 5.21x with the
late ones that return 1.96x. As long as the strong early increments
outweigh the weak late ones, the average stays above 5.0 even while the
next dollar is below it. The marginal audit measures the split: average
ROAS stays above target from \$1,000 to \$3,000 while marginal ROAS
falls below it after the first increment.

</details>

**3. What is the walk-away line, and who sets it?**

<details>
<summary>Answer</summary>

The ROAS (or CPA) below which the advertiser stops spending. The line is
the advertiser's, set by their own economics; the platform can only see
it when the budget moves. The platform's job is to slow the decay — via
relevance, placement, and measurement — because once the line is crossed,
the auction cannot bid the advertiser back, and the marginal dollar
crosses it before the average does.

</details>

## Next

The advertiser's return decays and its margin is hidden; stage 55 prices
the user lifecycle that feeds it. A detour from here: [the average hides
the margin](when-the-average-hides-the-margin/) — the executed cut read:
the marginal dollar returns 1.96x while the average says 5.21x, so a
budget cut from the top loses \$980 where the same cut from the first
increment loses \$2,604.

Another detour: [the marginal dollar buys less every
time](when-roas-collapses/) — the executed read: CPA climbs from \$3.23
to \$6.59 as spend doubles, and ROAS falls below the \$5 target.

Another detour: [the advertiser's exit is the platform's
loss](when-the-budget-moves/) — the executed read: when a rival channel
returns 4.6x and the platform 3.1x, the budget moves and platform
revenue falls by half.
