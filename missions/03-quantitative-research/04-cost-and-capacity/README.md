---
status: verified
level: applied
verified: 2026-07-27
label: Cost and capacity
---

# How much can the paper return actually carry?

**Before this:** [stage 03's purged, embargoed validation](../03-walk-forward-validation/)
— this stage only prices weights that already survived that boundary.

Your validated strategy makes 12% a year on paper. How much money can you put
into it before it makes nothing? Capacity is not a footnote. It is a property
of the strategy, and often the property that decides whether a signal is a
business. Stage 02, `02-cross-sectional-rank`, produces target weights and a
turnover series. Stage 03 checks the validation boundary. This stage makes the
economic boundary explicit before the report can compare a candidate with its
baselines.

The artifact is a capacity curve: net dollar return versus book size. The core
run fetches the same public Yahoo price path used by stage 00, now including
volume, for AAPL over two years. It measured 500 bars, USD 12,578,055,538 average
daily dollar volume, and 1.7839% realized daily volatility. The cost
assumptions and discrete curve output are recorded in
[`runs/2026-07-27-cost-capacity.md`](runs/2026-07-27-cost-capacity.md). Those
liquidity inputs are real; the impact parameters are not execution evidence. These figures come from a trailing window fetched on the run date; re-running the command pulls a newer window and shifts them slightly, which the run record explains.

## Which part of trading gets worse with size?

Pull the cost stack apart and you find different mechanisms at each layer.
Commission is roughly linear in dollars traded. Spread is the toll for
crossing the bid-ask market, and stays approximately a fixed number of basis
points while a trade remains small. Neither alone creates the familiar
capacity cliff — that comes from market impact, the price concession needed
to find the other side of an order. The common square-root model writes
impact as *Y × volatility × sqrt(participation)*, where participation is
trade notional divided by average daily volume.

Square root is sublinear in notional, but it is superlinear relative to zero:
impact per dollar rises as participation rises. Doubling a trade does not
double its impact fraction, yet it increases it by sqrt(2). That is enough to
make a larger book earn a lower percentage return. The model is an empirical
regularity fitted on particular markets and periods, not a physical law.
Almgren, Thum, Hauptmann, and Li, “Direct Estimation of Equity Market Impact,”
2005, fit a different exponent in one desk dataset; Tóth et al., “Anomalous
Price Impact,” 2011, motivate approximate square-root behavior. The form is
useful; its coefficient must be fitted from the firm’s fills.

Rebalance more often, or change more weight each time, and turnover converts
that per-trade cost into annual drag by paying the stack repeatedly. The core
script declares monthly rebalancing and six times annual one-way turnover: at
a USD 10m book it calculated 0.0398% participation per rebalance and 0.2780%
annual cost — 0.0300% commission, 0.1200% spread, 0.1280% impact. These are
measured outputs conditional on disclosed assumptions, not a brokerage bill.

<!-- interactive: CostCapacity -->

Move book size and turnover. The widget is an illustrative causal surface; its
measured defaults and the complete curve are in the run record. Hold the 12%
paper return fixed and the modeled net return falls as the liquidity bill
grows. A higher turnover collapses the ceiling even when alpha does not move.

## Where does another dollar stop helping?

Watch net percentage return as book size grows and it declines monotonically.
Net *dollar* return does something different: it first rises, then peaks,
then falls, and that peak is the capacity answer — past it, marginal net
return is zero or negative. On the declared 12% paper scenario, the script's
discrete sweep peaks at USD 25,156,111,076 and crosses total net-return
breakeven at USD 125,780,555,379. Those enormous values expose a
lesson-specific limitation, not an investable claim: a single high-ADV name
is not a portfolio, the curve allows implausible participation rates, and the
gross return is an assumption. A real capacity exercise imposes position,
participation, venue, and execution constraints long before interpreting
those levels.

A signal can survive stage 03 and still be worthless because capacity is below
the size at which anyone would operate it. That is not research failing. It is
research preventing an expensive story from becoming a strategy.

The capacity result is a decision boundary, not a recommendation. It can reject
a research claim before anyone spends time on execution engineering, but it
cannot price an actual order. Urgency, intraday volume shape, correlated
trading, borrow, taxes, and stress alter both the curve and feasible
participation. Naming those missing owners makes the next data task concrete.

Run `uv run python core/cost_capacity.py --ticker AAPL --range 2y --turnover 6`.
`prod/capacity_optimize.py` implements the production boundary: estimate Y from
timestamped fills and put expected costs inside a constrained optimization
objective. Subtracting costs after selecting weights yields a different,
worse portfolio because the optimizer never had the option to prefer a
slightly weaker signal that is much cheaper to trade.

## What this curve does not prove

Every impact coefficient, commission, spread tier, gross return, and cadence
here is assumed. This repository has no fills, quotes, order slices, or venue
outcomes; those are the data needed to fit the absolute level. The curve teaches
the shape and the ownership boundary. `05-report` next refuses to call the
mission met until net outcomes, both baselines, every guardrail, and regime
failures arrive as a complete artifact.

A detour from here: [where does the book stop making
money?](when-the-book-stops-making-money/) — the capacity curve swept across
the full book-size range: net dollar return peaks near \$31.6B, turns
negative at \$100B, and the cliff is where participation crosses 100% of
daily volume.
