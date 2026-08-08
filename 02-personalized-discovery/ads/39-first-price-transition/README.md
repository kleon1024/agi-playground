---
status: verified
level: applied
base: scratch
label: First-price transition
verified: 2026-08-07
---

# The bidder pays its own bid, so the estimate decides the net

**Question:** stage 14's auction was second-price, where the winner
pays the second bid. This stage asks what changes when the winner pays
its own bid and answers: bidding becomes shading — the bidder must
discount its true value, because the bid sets both the win probability
and the price — and the shade is an estimate of a competitor
distribution the bidder cannot see.

**Before this:** [stage 14 — ad auction](../14-ad-auction/) for
second-price truthfulness, and [stage 28 — auction
revenue](../28-auction-revenue/) for the rule change that moved the
industry from second to first price.

## The shading sweep, executed

The run ([record](runs/2026-08-07-first-price-transition.md)) sweeps
the bid factor against a unit value:

| factor | bid | win | net |
|---|---:|---:|---:|
| 1.00 | \$1.00 | 1.00 | \$0.00 |
| 0.80 | \$0.80 | 0.80 | \$0.16 |
| 0.60 | \$0.60 | 0.60 | \$0.24 |
| 0.50 | \$0.50 | 0.50 | \$0.25 |
| 0.40 | \$0.40 | 0.40 | \$0.24 |

In first price the winner pays its own bid, so net is (value - bid)
times win probability. Bid the full value and any win nets zero; shade
too much and wins disappear. With a uniform competitor the optimum is
half the value: bidding \$0.50 nets \$0.25, the peak of the executed
curve.

## The mechanism, named

The bid is now an estimation problem. In second price, truthful
bidding is optimal and the winner's payment reveals the competitor's
bid, so the market's shape is visible in the log. In first price, the
bidder must guess how much to shade, and nothing in its own outcomes
reveals the competition directly — a win shows only the price it paid
for its own bid. Google moved Ad Manager to unified first price in
September 2019, and the demand side that had relied on truthful
bidding had to relearn an estimation problem whose signal was
previously free (Vickrey 1961, J. Finance; Edelman, Ostrovsky &
Schwarz 2007, AER; Varian 2007, IJIO).

## The failure mode, named and audited

**Belief error is its own price.** The audit
([record](runs/2026-08-08-shading-error.md)) holds the bidder's belief
fixed — competitors uniform on [0, 1], bid 0.50 — and shifts the true
competitor distribution, the mis-specification a real bidder cannot
see:

| truth | win | realized net | optimal net | loss |
|---|---:|---:|---:|---:|
| U[0, 1] | 0.50 | 0.250 | 0.250 | 0.000 |
| U[0.3, 1.3] (stronger) | 0.20 | 0.100 | 0.122 | 0.022 |
| U[0, 0.4] (weaker) | 1.00 | 0.500 | 0.600 | 0.100 |

The loss is the square of the belief error divided by four: a belief
error of 0.3 costs 0.022 per auction, 9 percent of the stage's optimal
net of 0.25, and the direction matters — under-shading against
stronger competition loses wins, over-shading against weaker
competition wins everything but overpays. The verdict is measured:
**THE ESTIMATE DECIDES THE NET.** Shading is not a formula applied to
a known distribution; it is a prediction, and the prediction's error
lands directly in net value.

**The estimate is censored where the bidder never probes.** The
[competition-unobservable detour](when-the-competition-is-unobservable/)
measures where the belief comes from: the bidder fits the competitor
distribution from probed win rates, and each probe is an impression it
risks overpaying for, so probing is rationed. At 100 trials per probe
the estimated optimum wanders to 0.60 and the realized net loses 0.011
per auction — 4.4 percent of the optimum — against 0.001 at 1,000
trials. The second-price log used to deliver that signal for free;
first-price censored it, which is why bid-landscape forecasting became
its own industrial problem after the 2019 transition.

**The platform's revenue forecast carries the same error.** The
[market-adjustment detour](when-the-market-adjusts/) reads revenue as
bidders learn: \$0.95 per auction under naive bidding falls to \$0.42
once bidders shade, so a launch-day forecast that assumes naive
bidding overstates the steady state by more than half.

## The fix and its trade

The fix is to treat shading as a prediction: probe the competitor
landscape, fit the distribution the second-price log used to reveal for
free, and hedge the estimate's uncertainty in the bid policy. The audit
prices the belief-error cost — a belief error of 0.3 costs 0.022 per
auction against the 0.250 optimum, and mis-specifying weaker competition
(U[0, 0.4]) loses 0.100 — and the probe-budget row shows where the fix
lives: 100 trials per probe wanders the fitted optimum to 0.60 and
loses 0.011 per auction, against 0.001 at 1,000 trials.

The trade is that probing is rationed and the market moves. Every probe
is an impression the bidder risks overpaying for, so the landscape
estimate is always built on less data than the second-price log gave,
and the platform's revenue forecast carries the same error: \$0.95 per
auction under naive bidding settles at \$0.42 once bidders shade, so a
launch-day forecast that assumes naive bidding overstates the steady
state by more than half. The forecasting team must assume learned
shading, not the rule change, and the reserve is the cushion that buys
time while the demand side relearns.

## Who owns the loop

The estimate, the rule, and the forecast are owned by three different
teams, and each owner is tied to one of the failure modes above:

- **The demand-side bidding team** owns the shading estimate: the
  probe budget, the fitted landscape, and the bid policy that hedges
  the estimate's uncertainty. It owns the belief-error failure — the
  audit's 0.022 loss per auction is a bid-policy defect, and the
  detour's 100-trials row shows the probing budget that produced it.
- **The auction and pricing team** owns the rule that made the bid the
  price, the reserve floor that cushions the transition, and the
  market-adjustment curve the transition sets in motion. It owns the
  launch-day-vs-settled failure — the revenue number it committed to
  was the transient, not the equilibrium.
- **The measurement and forecasting team** owns the revenue forecast
  and must assume learned shading, not naive bidding. It owns the
  forecast error the market-adjustment detour measures: \$0.95 assumed
  against \$0.42 settling is a forecast failure before it is a
  pricing one.

When the ownership is implicit, the bidding team ships a point
estimate nobody hedges, the pricing team reads launch-day revenue as
steady state, and the forecast team reports the number the market
already left behind.

## Why this belongs in the mission

The ad market's transition from second to first price changed the
bidder's core decision: truthfulness stopped being optimal, and the
whole demand side had to relearn bidding. Stage 28 compared the rules;
this stage prices the transition's cost — not the rule itself, but the
estimation problem the rule created. That is the mission's frontier
claim for the auction: after 2019 the bid is a prediction, and the
mission's discipline applies — the prediction is only as good as the
measured signal it was fit to, which is the same evidence rule the
rest of the track holds against its models.

## Evidence boundary

The executed sweep and the audit's mis-specification runs are
illustrative and deterministic over declared values and win models
(uniform competitors, fixed seed). They demonstrate the mechanism and
the estimation cost; real bidding needs the actual competitor
distribution, which is unobservable, so the numbers a live bidder
would see depend on the true landscape and its probe policy. The
Google Ad Manager rollout (2019-09-04) and the auction-theory
citations are attributed as published.

## Check your mental model

Answer each before opening it.

**1. Why is bidding the full value a losing strategy in first price?**

<details>
<summary>Answer</summary>

Because the bid is the price. A win at the full value pays everything
the impression is worth to the bidder — net is exactly zero, and a
second-price bidder used to winning at the second price now pays its
own bid. The executed run shows it directly: bidding \$1.00 wins
everything and nets \$0.00.

</details>

**2. Why is the optimum half the value here?**

<details>
<summary>Answer</summary>

Because with a uniform competitor, shading to half the value balances
the two losses. Under-shading wins more but pays too much; over-shading
keeps more margin but loses auctions. The product (value - bid) times
win probability peaks at the halfway bid — \$0.50 nets \$0.25, above
both \$0.80's \$0.16 and \$0.40's \$0.24.

</details>

**3. Why does a mis-estimated competitor distribution cost money even
when the bidder shades at its believed optimum?**

<details>
<summary>Answer</summary>

Because the believed optimum is only optimal against the believed
distribution. Against stronger competition (truth U[0.3, 1.3]) the
0.50 bid wins just 20 percent of auctions; against weaker competition
(truth U[0, 0.4]) it wins everything but nets 0.50 against a 0.60
optimum. The audit's loss curve is d-squared-over-four, so a belief
error of 0.3 costs 0.022 per auction — the estimate's error, not the
rule, decides the net.

</details>

## Next

The frontier ads track continues. Next is [stage 40 — privacy-safe
attribution](../40-privacy-safe-attribution/), where measurement
survives differential privacy.

A detour from here: [the competition the bidder never probes never
reaches the estimate](when-the-competition-is-unobservable/) — the
executed estimation read: at 100 trials per probe the fitted curve
moves the optimum to 0.60 and loses 0.011 per auction, and the
second-price log that used to reveal competitor bids for free is gone.

Another detour: [the shading is wrong and the error is a direct
cost](when-the-shading-is-wrong/) — the executed read: under-shading
at \$0.80 wins more but nets \$0.16, over-shading at \$0.20 loses
auctions, and both lose to the \$0.50 optimum's \$0.25.

Another detour: [the market adjusts as bidders learn to
shade](when-the-market-adjusts/) — the executed read: platform revenue
per auction falls from \$0.95 under naive bidding to \$0.42 once
bidders shade, so a forecast that assumes naive bidding overstates the
steady state.
