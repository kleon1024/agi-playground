---
status: verified
level: applied
base: scratch
label: When the average hides the margin
verified: 2026-08-08
---

# The average hides the margin, and the budget cuts the wrong dollar

**Question:** [stage 54's advertiser ROAS](../) tracks the lifecycle
decay. This chapter reads the executed marginal audit and asks the
failure mode that average ROAS hides: the advertiser scales and cuts at
the margin, and a return that clears the target on average can be below
it on the next dollar — so the average-guided budget spends where it
should stop and cuts the wrong dollar when it shrinks.

**Before this:** [stage 54 — advertiser ROAS](../) and its executed
weekly lifecycle read, plus the [ROAS-collapse
detour](../when-roas-collapses/) for the marginal decay at scale.

## The cut decision, executed

The run ([record](runs/2026-08-08-cut-the-marginal-dollar.md))
measures, for each \$500 increment and for the whole budget, the
revenue lost per dollar of spend cut:

| cut | spend cut | conversions lost | revenue lost | return per \$ cut |
|---|---:|---:|---:|---:|
| \$1,000-1,500 | \$500 | 93 | \$2,604 | 5.21 |
| \$1,500-2,000 | \$500 | 70 | \$1,960 | 3.92 |
| \$2,000-2,500 | \$500 | 50 | \$1,400 | 2.80 |
| \$2,500-3,000 | \$500 | 35 | \$980 | 1.96 |
| all \$3,000 | \$3,000 | 558 | \$15,624 | 5.21 |

Every row saves the same \$500, but the revenue lost falls from
\$2,604 to \$980 — the marginal dollar returns 1.96x while the first
returns 5.21x; cutting the whole budget loses \$15,624, the average.

## The failure mode, named and audited

**Deciding the budget on the average hides which dollar is losing.**
Average ROAS mixes dollars that return 5.21x with dollars that return
1.96x, so it clears the target at every spend level while the marginal
dollar is already below it. The stage audit
([record](../runs/2026-08-08-marginal-roas.md)) measures the gap:
average ROAS stays above 5.0 from \$1,000 to \$3,000, while marginal
ROAS clears the target only on the first increment and falls to 1.96
on the last. The verdict is measured: **THE AVERAGE HIDES THE MARGIN —
THE BUDGET DECIDED ON AVERAGE ROAS KEEPS SPENDING WHERE THE NEXT
DOLLAR ALREADY LOSES.**

**The same blindness cuts the wrong dollar.** When the budget shrinks,
the average-guided advertiser cuts in proportion or from the
cheapest-to-explain line, losing revenue the marginal accounting would
have kept. The executed cut table prices the difference: a \$500 cut
from the top loses \$980 (1.96x), while the same cut from the first
increment loses \$2,604 (5.21x). Cutting the top is the least revenue
lost per dollar saved — and lifts the remaining average ROAS from 5.21
to 5.86 — because the dollar that returns the least is the one the
budget should have stopped at first.

**The average is also how incrementality gets misread.** The reported
return over-credits the dollars that would have converted anyway:
eBay's field experiment cut paid search ads and sales barely moved for
most queries, so the measured incremental return was far below the
reported average (Blake, Nosko, and Tadelis 2015, "Consumer
Heterogeneity and Paid Search Effectiveness: A Large-Scale Field
Experiment", Econometrica 83(1):155-174, doi 10.3982/ECTA12423).
Measuring the marginal dollar is hard on purpose: Lewis and Rao (2015,
"The Unfavorable Economics of Measuring the Returns to Advertising",
Quarterly Journal of Economics 130(4):1941-1973, doi 10.1093/qje/qjv023)
showed that even 25 large experiments spanning about \$2.8 million of
ad spend leave estimated returns too imprecise to guide a budget, so
most advertisers never see the curve this audit assumes.

## The fix and its trade

The fix is marginal accounting on both sides of the budget: set the
spend level where the marginal dollar stops clearing the target, and
when the budget must shrink, cut from the top increment first —
measured, not proportional. Google's bid systems optimize the same way,
allocating spend at the margin rather than against the campaign average
("Optimize for marginal ROI instead of average ROI", Google Ads support,
support.google.com/google-ads/answer/12850633, consulted 2026-08-08).
The trade is that the marginal curve is expensive to see: it needs
incrementality experiments per segment and channel, which are slow and
noisy — Lewis and Rao is the warning that the measurement itself can be
too imprecise to trust. Until the curve is measured, the two rules
disagree by exactly the dollars that are hardest to defend: the ones
that return 1.96x while the report says 5.21x.

## Who owns the loop

- **The advertiser's media buyer** owns the cut decision at the margin:
  scaling against the marginal target and cutting from the top
  increment first, not in proportion.
- **The platform's measurement team** owns the marginal curve per
  segment and channel, produced by the incrementality experiments that
  are the only honest source.
- **Finance and ads-operations** owns the marginal reporting — the
  number that shows the 1.96x dollar next to the 5.21x average, so the
  budget is not decided against a confidently wrong average.

## Evidence boundary

The executed cut table and the stage audit run over a declared concave
conversion curve (illustrative, deterministic, fixed \$28 AOV). Real
budget and cut decisions need the measured marginal conversion curve
per segment and the advertiser's actual marginal target. The Blake,
Nosko and Tadelis, Lewis and Rao, and Google Ads citations are
attributed as published or as consulted on the date shown.

## Check your mental model

Answer each before opening it.

**1. Why does the average clear the target while the marginal dollar
loses?**

<details>
<summary>Answer</summary>

Because the average mixes the early dollars that return 5.21x with the
late ones that return 1.96x. As long as the strong early increments
outweigh the weak late ones, the average stays above 5.0 even while
the next dollar is below it — the report and the decision disagree
exactly where the advertiser walks away.

</details>

**2. Which dollar should a budget cut remove first, and why?**

<details>
<summary>Answer</summary>

The top increment: the one that returns the least. In the executed
table cutting \$2,500-3,000 saves \$500 and loses \$980, while cutting
the first increment loses \$2,604 for the same saving. The marginal
dollar goes first because it is the one the budget should have stopped
at first, and cutting it lifts the average ROAS that remains.

</details>

**3. Why can the platform not just report the marginal return?**

<details>
<summary>Answer</summary>

Because the marginal return is the hardest number to measure: it needs
incrementality experiments per segment and channel, and Lewis and Rao
showed those can be too noisy to guide a budget even at millions of
dollars of spend. The average is cheap to compute and confidently
wrong; the margin is expensive to measure and right.

</details>

## Next

Back to [stage 54](../). The
[ROAS-collapse detour](../when-roas-collapses/) is the decay that
creates the margin, and the
[budget-moves detour](../when-the-budget-moves/) is what happens when
the advertiser reallocates on the measured number.
