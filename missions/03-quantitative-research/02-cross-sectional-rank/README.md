---
status: verified
level: applied
verified: 2026-07-27
label: Cross-sectional rank
---

# What turns a score into a portfolio?

**Question:** a candidate signal scores every name in the universe. What turns
that score into a portfolio, and how many of the choices in that translation
are part of the strategy rather than an afterthought?

**Before this:** [stage 01's candidate signals and search log](../01-signal-research/).

[Stage 01](../01-signal-research/) produced candidate signals plus a
machine-readable search log. It did not produce a tradable decision. This stage
holds one momentum score fixed and changes only its translation into target
weights. The result is the central fact to retain: sizing is co-equal with the
signal. Two sizing rules applied to the same scores are two strategies, with
different concentrations, turnover, costs, and capacity.

## Rank because levels drift

A raw score does not arrive with a stable unit. In the recorded panel, the
cross-sectional momentum mean was 0.168 with 0.353 standard deviation at the
first displayed date, then 0.300 and 0.312 at the last. A fixed dollar weight
per raw-score unit would silently change its effective aggressiveness as that
scale changes. Cross-sectional ranks discard the level and retain order: the
best name is at the top percentile and the worst at the bottom on every date.
That makes the mapping robust to monotone rescaling and regime-dependent spread.

The exchange is deliberate. A rank cannot tell whether the top two names are
almost tied or widely separated. Using it asserts that relative order is
trustworthy while score magnitude is not. Signal-proportional sizing makes the
stronger assertion that magnitude contains useful information. Neither is a
default supplied by mathematics; each is a research hypothesis that belongs in
the disclosed strategy definition and, if varied, the search log.

## Choose the belief encoded by the weights

The sizing ladder exposes four distinct beliefs. Equal-weight decile holds only
the extreme long and short names: it claims the signal is informative at tails,
not in between. Rank-proportional holds the full universe using centered ranks:
every rank step gets equal importance. Signal-proportional weights a z-scored
raw signal, claiming larger scores deserve larger conviction. Volatility-scaled
starts there and divides by trailing realized volatility, trading some
conviction-following for more even risk contribution.

All raw rules are normalized to gross exposure 2.0, meaning one unit long and
one unit short. That isolates the effects of shape rather than allowing an
arbitrary leverage difference to explain them. The recorded unconstrained run
makes the contrast visible: equal-weight decile had HHI 0.6667 and monthly
turnover 0.638; rank-proportional had HHI 0.1776 and turnover 0.348;
signal-proportional had HHI 0.2243 and turnover 0.369; volatility-scaled had
HHI 0.1952 and turnover 0.404. These are measurements of this paper exercise,
not expected market outcomes.

<!-- interactive: CrossSectionalWeights -->

The widget defaults to that run. Hold the score vector fixed and select a
different rule: the composition changes even before prices move. It is not a
prediction interface. It is a view of the measured consequence of choosing a
weighting belief.

## Constraints change the strategy again

Long-short construction removes broad market direction, which can make a weak
cross-sectional effect easier to inspect. It also gives up a source of return
and does not neutralize sector, factor, liquidity, or crowding exposure by
itself. Real books therefore carry constraints: a per-name cap limits any one
position, sector neutrality de-means weights inside each sector, and a turnover
budget limits trading between rebalances.

These cannot be treated as a final clipping pass. In the core demonstration,
cap then sector de-mean sometimes pushes positions above the cap again: it
recorded 7 post-neutralization cap violations for equal-weight decile, 47 for
rank-proportional, 35 for signal-proportional, and 43 for volatility-scaled.
Gross exposure also falls after naïve clipping because discarded notional is not
redistributed. A constrained optimizer expresses caps and neutrality together;
`prod/pandas_optimizer_rank.py` shows that contract. Post-hoc clipping silently
breaks either the cap, the neutrality, the target gross, or all three.

Sector labels need their own availability timestamp. A classification obtained
today can be revised after a spin-off, merger, or reclassification. Using it
backward would reintroduce exactly the point-in-time look-ahead that [stage
00](../00-market-data/) removed from prices and fundamentals.

## Run the paper portfolio

```bash
uv run python core/cross_sectional_rank.py --range 3y --top-frac 0.1 --cap 0.10
```

The standard-library core fetches a 30-name public price panel, computes
12-month-minus-one-month momentum from past closes only, forms month-end paper
weights, and reports gross exposure, concentration, turnover, and paper Sharpe
for raw and constrained rules. The cap and top-decile defaults are stated
inputs, not parameters searched to produce a favorable output. See the recorded
[run](runs/2026-07-27-core-cross-sectional-rank.md). These figures come from a trailing window fetched on the run date; re-running the command pulls a newer window and shifts them slightly, which the run record explains.

The production companion uses pandas for cross-sectional grouping and cvxpy for
joint cap, neutrality, and gross constraints. Other valid production optimizers
include SciPy's constrained solvers and commercial portfolio-optimization
systems. They make a constraint solution auditable; they do not establish that
the input signal works.

## Evidence boundary and the next attack

Every return here is a cost-free, capacity-free paper return. It is therefore
an upper bound that [stage 04](../04-cost-and-capacity/) can only reduce, never
validate. The reported paper Sharpes are included to show how sizing changes a
paper series; they do not establish profitability, live performance, or
implementability. [Stage 03](../03-walk-forward-validation/) first asks whether
any such result survives the disclosed search and a purged, embargoed
out-of-sample evaluation. Only then does it make sense to ask how much survives
trading costs and market impact.
