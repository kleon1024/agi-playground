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

Watch a raw score arrive with no stable unit. In the recorded panel, the
cross-sectional momentum mean was 0.168 with 0.353 standard deviation at the
first displayed date, then 0.300 and 0.312 at the last. Size a fixed dollar
weight per raw-score unit and its effective aggressiveness silently changes as
that scale drifts. Rank the cross-section instead and you discard the level
but keep the order: the best name sits at the top percentile and the worst at
the bottom on every date, which makes the mapping robust to monotone
rescaling and regime-dependent spread.

The exchange is deliberate. A rank cannot tell whether the top two names are
almost tied or widely separated. Using it asserts that relative order is
trustworthy while score magnitude is not. Signal-proportional sizing makes the
stronger assertion that magnitude contains useful information. Neither is a
default supplied by mathematics; each is a research hypothesis that belongs in
the disclosed strategy definition and, if varied, the search log.

## Choose the belief encoded by the weights

Walk the sizing ladder and four distinct beliefs come into view. Equal-weight
decile holds only the extreme long and short names, claiming the signal is
informative at the tails and not in between. Rank-proportional holds the full
universe on centered ranks, giving every rank step equal importance.
Signal-proportional weights a z-scored raw signal, claiming larger scores
deserve larger conviction. Volatility-scaled starts from that and divides by
trailing realized volatility, trading some conviction-following for more even
risk contribution.

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

Remove broad market direction with long-short construction and a weak
cross-sectional effect becomes easier to inspect — but that also gives up a
source of return, and it does not by itself neutralize sector, factor,
liquidity, or crowding exposure. Real books carry constraints on top: a
per-name cap limits any one position, sector neutrality de-means weights
inside each sector, and a turnover budget limits trading between rebalances.

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

## The fix and its trade

The failure is that sizing is co-equal with the signal, and the constraint
step re-breaks what it claims to enforce. The recorded run holds one
momentum score fixed and changes only its translation into target weights:
equal-weight decile and rank-proportional moved concentration from HHI
0.6667 to 0.1776 and turnover from 0.638 to 0.348, while paper Sharpe
spanned -0.68 to -1.20 across the four rules — two sizing rules applied to
the same scores are two strategies. Applying a cap and then de-meaning
inside each sector pushed positions back above the cap: 7 re-breaches for
equal-weight decile, 47 for rank-proportional, 35 for signal-proportional,
43 for volatility-scaled, and gross exposure fell from 2.00 to between
0.16 and 1.32 because discarded notional is never redistributed. The
cap-bites detour adds the policy's second failure: the cap binds only below
0.25 on this universe, so a looser cap is an inert policy and a tighter one
a hidden tax.

The fix is a joint constrained optimizer — `prod/pandas_optimizer_rank.py`
expresses cap, sector neutrality, and gross exposure in one pass, with
SciPy's constrained solvers and commercial portfolio-optimization systems
as alternatives — plus an availability timestamp on sector labels, so a
reclassification obtained today cannot leak backward into a historical
book. The trade is transparency and speed for constraint correctness: the
sequential pipeline is readable line by line but silently breaks a
constraint it claims to enforce, and the optimizer moves the audit point
from a list of re-breach violations to a single declared contract. The
optimizer makes the constraint solution auditable; it does not establish
that the input signal works.

## Who owns the loop

- **Research** owns the sizing rule: the weighting belief — order, rank
  step, or magnitude — is a hypothesis that belongs in the disclosed
  strategy definition and, if varied, in the search log.
- **Portfolio construction** owns the constraint pipeline: the optimizer,
  the gross-exposure normalization, and the joint cap/neutrality contract
  that replaces post-hoc clipping.
- **Risk** owns the cap policy and its violation check: where the cap
  binds on the current universe, what a re-breach costs, and whether the
  policy is doing anything at all — nothing changes above 0.25, and a cap
  that never binds is a policy that does nothing.

When the ownership is implicit, research picks a rule, construction clips
weights after the fact, and risk reports a cap that silently re-breaks —
and nobody owns the strategy that the sizing decision actually created,
the symptom this stage opened with.

## Evidence boundary and the next attack

Every return here is a cost-free, capacity-free paper return. It is therefore
an upper bound that [stage 04](../04-cost-and-capacity/) can only reduce, never
validate. The reported paper Sharpes are included to show how sizing changes a
paper series; they do not establish profitability, live performance, or
implementability. [Stage 03](../03-walk-forward-validation/) first asks whether
any such result survives the disclosed search and a purged, embargoed
out-of-sample evaluation. Only then does it make sense to ask how much survives
trading costs and market impact.

A detour from here: [what does the position cap actually
cost?](when-the-cap-bites/) — the cap swept across five values: it binds
only below 0.25 on this universe, trades exposure for diversification
without improving Sharpe, and taxes tightness with re-breach violations.

The model's structure, drawn: [the sizing rule IS the
strategy](the-rank-that-becomes-a-position/) — the signal->rank->weight->
position pipeline read from the recorded run: the same signal becomes four
different portfolios under four sizing rules, and every rule breaks the
cap after sequential cap-then-de-mean.
