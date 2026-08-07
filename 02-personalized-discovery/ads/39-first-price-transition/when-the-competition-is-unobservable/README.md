---
status: verified
level: applied
base: scratch
label: When the competition is unobservable
verified: 2026-08-08
---

# The competition the bidder never probes never reaches the estimate

**Question:** [stage 39's first-price bidder](../) shades against a
competitor distribution it cannot see. This chapter reads the
executed estimation audit and asks where that estimate comes from —
and what the first-price rule change took away from it.

**Before this:** [stage 39 — first-price transition](../) and its
executed shading-error audit, and [stage 28 — auction
revenue](../../28-auction-revenue/) for the rule change that made the
bid the price.

## The estimation, executed

The run ([record](runs/2026-08-08-competition-estimation.md)) probes
win rates at nine bids, fits a piecewise-linear competitor CDF, and
bids the optimum against the estimate, over four probe budgets:

| trials per probe | estimated optimum | realized net | loss vs 0.25 |
|---:|---:|---:|---:|
| 100 | 0.60 | 0.239 | 0.011 |
| 1,000 | 0.50 | 0.249 | 0.001 |
| 10,000 | 0.52 | 0.249 | 0.001 |
| 100,000 | 0.50 | 0.249 | 0.001 |

At 100 trials per probe the noisy win-rate curve moves the estimated
optimum ten cents off and the realized net loses 4.4 percent of the
0.25 the truth allows. Ten times the probes converge.

## The failure mode, named and audited

**First-price removed the free signal, and probing is rationed.** In a
second-price auction every win reveals the competitor's bid — the
winner's log estimates the distribution with no extra spend. In
first-price the winner pays its own bid, so a win reveals nothing
about the competition; the only signal is the win-rate curve, and each
probe bid is an impression the bidder risks overpaying for (a probe at
0.90 wins almost everything and pays too much, so launch-phase bidders
ration their probes and the fitted curve carries noise). The executed
table prices that rationing: the 100-trials row wanders and loses,
and the 0.011 loss is the stage audit's belief-error curve measured at
its source. This is why the unified-first-price transition (Google Ad
Manager, September 2019) created the industrial problem of bid
landscape forecasting: the signal every bidder used to get for free
now has to be bought with probing or inferred from censored outcomes
(Vickrey 1961, J. Finance; Edelman, Ostrovsky & Schwarz 2007, AER;
Varian 2007, IJIO).

**The estimate's error, not the estimate, is the decision input.** The
stage audit already showed the loss is the square of the belief error
divided by four — a belief error of 0.3 costs 0.022 per auction, 9
percent of the optimum. This detour measures how that error enters:
the bidder does not mis-estimate because it is sloppy; it
mis-estimates because the log is censored at its own bids and the
probe budget is a spend decision. The fix is not a better shading
formula — it is buying enough signal, or switching to a rule that
extracts signal from outcomes the bidder already pays for.

## The fix and its trade

The fix is to treat the competitor distribution as an estimand with a
budget: allocate a fraction of impressions to probing (a bid-noise
exploration policy), keep the probe grid wide enough to see the upper
tail, and refit the landscape on a schedule instead of once at launch.
The trade is that probing is real spend with no guarantee of a win at
a good price — the 0.90 probe wins nearly everything and overpays,
which is margin the estimation phase burns, and the same exploration
that improves the estimate lowers the launch-phase net. A cheaper
alternative is to borrow structure: assume a parametric family
(lognormal competitors) and fit it to censored wins with an
expectation-maximization step, which uses the losing auctions' bid
levels too — at the price of a model-class risk, exactly the
mis-specified-world row of the stage audit where the truth does not
live in the assumed family.

## Evidence boundary

The executed probing audit over declared probe budgets (illustrative,
deterministic, fixed seed, uniform competitor) demonstrates the
estimation mechanism; real bid-landscape estimation needs the actual
bid distribution, the auction's price feedback (win price, losing
price floors where the exchange reveals them), and a measured
probe-spend-versus-error trade from the live market. The Google Ad
Manager unified-first-price rollout (2019) and the auction-theory
citations are attributed as published.

## Check your mental model

Answer each before opening it.

**1. Why can the first-price winner's log not estimate the
competition the way the second-price log could?**

<details>
<summary>Answer</summary>

Because the payment reveals different information. A second-price win
reveals the competitor's bid — the price paid — so the log contains
direct samples of the distribution. A first-price win reveals only the
bidder's own bid, so the log contains no competitor information at
all; the bidder must probe win rates with real bids, and each probe
risks overpaying, which is why probing is rationed and the estimate
carries noise.

</details>

**2. What does the 100-trials row of the audit actually measure?**

<details>
<summary>Answer</summary>

The price of a noisy estimate. With 100 trials per probe the fitted
win-rate curve wanders, the estimated optimum lands at 0.60 instead of
0.50, and the realized net loses 0.011 per auction — 4.4 percent of
the 0.25 the truth allows. It is the stage audit's d-squared-over-four
loss measured from where the d comes from: censored outcomes and a
rationed probe budget, not a bad formula.

</details>

## Next

Back to [stage 39](../). The
[market-adjustment detour](../when-the-market-adjusts/) shows the
aggregate side of the same estimate: as every bidder learns to shade,
the platform's revenue falls and the landscape the bidder fits moves
under it.
