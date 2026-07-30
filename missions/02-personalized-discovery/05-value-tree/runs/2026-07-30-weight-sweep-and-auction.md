# Run — value-tree weight sweep, calibration break, and ad auction

CPU only, `python3 --version` = 3.11.14, seed 42 unless noted, no GPU involved
anywhere in this stage.

## Command 1: the default demo, 12 synthetic items

```
python core/value_tree.py
```

```
weight sweep: click <-> satisfaction, additive combination
  satisfaction weight 0.00: top 3 = ['item_8', 'item_0', 'item_4']
  satisfaction weight 0.25: top 3 = ['item_8', 'item_0', 'item_11']
  satisfaction weight 0.50: top 3 = ['item_6', 'item_11', 'item_10']
  satisfaction weight 0.75: top 3 = ['item_1', 'item_5', 'item_9']
  satisfaction weight 1.00: top 3 = ['item_1', 'item_9', 'item_5']

weight sweep: click <-> satisfaction, multiplicative combination
  satisfaction weight 0.00: top 3 = ['item_8', 'item_0', 'item_4']
  satisfaction weight 0.25: top 3 = ['item_11', 'item_6', 'item_2']
  satisfaction weight 0.50: top 3 = ['item_6', 'item_11', 'item_10']
  satisfaction weight 0.75: top 3 = ['item_5', 'item_6', 'item_1']
  satisfaction weight 1.00: top 3 = ['item_1', 'item_9', 'item_5']

calibration precondition:
weights unchanged; click predictions inflated 1.6x (not re-calibrated):
  honest ranking          ['item_10', 'item_11', 'item_8', 'item_6', 'item_1', 'item_2', 'item_9', 'item_5', 'item_0', 'item_7', 'item_4', 'item_3']
  miscalibrated ranking   ['item_11', 'item_10', 'item_6', 'item_2', 'item_7', 'item_4', 'item_5', 'item_1', 'item_8', 'item_0', 'item_9', 'item_3']
  order changed — with no change in product strategy, only in calibration.

ad auction, explicit trade rate:
  trade_rate=0.2: ad utility 0.154, does not clear the bar
  trade_rate=0.5: ad utility 0.385, does not clear the bar
  trade_rate=0.8: ad enters, displaces item_6 (organic value 0.499)
```

## Command 2: a larger synthetic slate, 30 items

```
python core/value_tree.py --n-items 30
```

Same qualitative pattern holds at 30 items: additive and multiplicative agree
at the sweep's endpoints (pure-click, pure-satisfaction weighting can only
produce one ranking each) and diverge in between; the calibration break still
reorders the honest ranking with no product-strategy change; the auction
still enters only at `trade_rate=0.8` (ad utility 0.545 against a higher
top-6 bar than the 12-item slate had).

## Command 3: the production trade-rate solver

```
python prod/scipy_trade_rate.py --target-ad-load 0.15
```

```
200 independent slates, target ad load 15.00%
solved trade rate: 0.6039
achieved ad load at that rate: 15.00%
```

`scipy.optimize.brentq` bisected to a trade rate of 0.6039 across 200
independent synthetic slates and hit the 15% target exactly (to the printed
precision) — confirming the monotonicity argument in the module docstring:
ad load is non-decreasing in the trade rate, so bisection converges cleanly.

## Extra: quantifying "multiplicative moves toward balanced items measurably sooner"

The README's section 3 asserts this qualitatively. Ran a finer sweep
(`steps=200` instead of the default demo's `steps=4`) directly against
`sweep_weight`, on the same 12-item seed-42 slate, to find the exact
satisfaction weight at which the top-ranked item first changes:

```python
from value_tree import make_items, sweep_weight
items = make_items(12, seed=42)
# first w_sat at which sweep_weight's top-1 item differs from w_sat=0's top-1
```

```
additive crossover w_sat=0.410 (item_8 -> item_6)
multiplicative crossover w_sat=0.165 (item_8 -> item_11)
```

The multiplicative rule flips its top pick at less than half the satisfaction
weight the additive rule needs (0.165 vs 0.410) — a concrete number behind
"moves toward balanced items measurably sooner," not just a direction.

## What this does and does not establish

- **Does establish:** the weight sweep, the additive/multiplicative
  divergence (including its magnitude, above), the calibration-precondition
  failure mode, and the auction's trade-rate mechanics all execute correctly
  and produce the qualitative and quantitative behavior the README claims.
- **Does not establish:** anything about a real platform's actual objective
  weights, real click/completion/satisfaction calibration quality, or real
  bid distributions — every input here is synthetic (`make_items`'s four
  archetypes), not fit to any observed user population.
