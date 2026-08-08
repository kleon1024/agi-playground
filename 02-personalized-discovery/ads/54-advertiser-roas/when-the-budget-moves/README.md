---
status: verified
level: applied
base: scratch
label: When the budget moves
verified: 2026-08-07
---

# The advertiser's exit is the platform's loss

**Question:** [stage 54's lifecycle](../) decays the return. This chapter
asks what happens when the advertiser acts on it, and answers: the
advertiser allocates by measured ROAS, so the platform's revenue falls
with the share — and the auction cannot bid the advertiser back once
their measured return says leave.

**Before this:** [stage 54 — advertiser ROAS](../) and its executed
weekly lifecycle read.

## The reallocation, executed

The run ([record](runs/2026-08-07-budget-moves-read.md)) splits the
advertiser's weekly budget by measured ROAS against a rival channel:

| platform share | platform revenue |
|---|---:|
| 100% | \$2,000 |
| 75% | \$1,500 |
| 50% | \$1,000 |
| 25% | \$500 |

## The reading

The platform's revenue is the advertiser's spend, and the advertiser
allocates by measured ROAS. When the rival channel returns 4.6x and the
platform 3.1x, the share moves and platform revenue falls by half. The
auction prices a slot; it cannot price the advertiser's overall return —
that is a product decision about relevance and placement. The exit is
not a bidding failure; it is the measurement of the platform's own
return losing to another channel's.

## The fix and its trade

The fix is honest incrementality on both sides. The platform reports
the measured incremental return instead of the attributed one, so the
advertiser's allocation is set against the number that survived an
experiment — stage 30's discipline, and the eBay field experiment is
the warning: paid search ads cut, sales barely moved for most queries,
so the attributed average had over-credited the ads (Blake, Nosko, and
Tadelis 2015, "Consumer Heterogeneity and Paid Search Effectiveness: A
Large-Scale Field Experiment", Econometrica 83(1):155-174, doi
10.3982/ECTA12423). The advertiser's fix is to allocate on marginal or
incremental return rather than the channel average, which is how modern
bid systems already optimize ("Optimize for marginal ROI instead of
average ROI", Google Ads support,
support.google.com/google-ads/answer/12850633, consulted 2026-08-08).
The trade is that incrementality is the expensive, slow measurement:
every allocation decision waits on an experiment, and while the numbers
are imprecise — Lewis and Rao (2015, "The Unfavorable Economics of
Measuring the Returns to Advertising", Quarterly Journal of Economics
130(4):1941-1973, doi 10.1093/qje/qjv023) found even large experiments
leave returns too noisy to guide budgets — the platform can lose share
to a rival channel's confidently wrong average before its own honest
number is ready.

## Who owns the loop

- **The platform's measurement team** owns the honest incrementality
  that the advertiser's allocation is set against — the attributed
  average over-credits the ads until an experiment corrects it.
- **The advertiser's media buyer** owns the allocation on marginal or
  incremental return across channels, the decision that moves the
  platform's revenue.
- **The ads product team** owns the relevance and placement that change
  the measured return itself — the only lever that can win the
  advertiser back once measured return says leave.

## Evidence boundary

The executed split over declared ROAS values (illustrative,
deterministic). It demonstrates the mechanism; real budget allocation
needs the measured cross-channel ROAS, the advertiser's attribution
window, and the platform's own incrementality — the number only an
experiment (stage 30) can produce.

## Check your mental model

Answer each before opening it.

**1. Why does platform revenue fall by half at a 50% share?**

<details>
<summary>Answer</summary>

Because revenue is the advertiser's spend: \$2,000 at full share becomes
\$1,000 at half, with no auction involved. The advertiser is not paying
less per impression; they are serving fewer impressions on this platform
because measured ROAS says the rival channel returns more. The loss is
portfolio allocation, and it moves on the measurement, not on the bid.

</details>

**2. Why can the auction not win the advertiser back?**

<details>
<summary>Answer</summary>

Because the auction prices a slot; the advertiser's decision is priced in
return on total spend across channels. A cheaper slot raises ROAS only
if it delivers real conversions — which is a relevance and placement
question, not a price one. Once measured return says leave, only the
product (and stage 30's honest incrementality) can change the number the
budget is allocated against.

</details>

## Next

Back to [stage 54](../). The [ROAS-collapse detour](../when-roas-collapses/)
is the decay that triggers the move: the marginal dollar stopping paying
as spend scales.
