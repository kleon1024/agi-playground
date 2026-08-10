# Run — demand elasticity, does the curve set the revenue peak

**Date:** 2026-08-08
**Command:** `uv run python core/elasticity_sweep.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 42's executed sweep prices the take rate on one volume-response
curve, `volume = 1000 x (1 - 1.6 x rate)`, which reproduces its table
(peak around 31 percent, \$154 at 35 percent). This audit asks the
industrial question that single curve skips: the optimal take rate is
not a number, it is a function of how fast transactions leave when the
cut rises. The run sweeps the elasticity slope k and measures where the
revenue peak sits on each curve, what the stage's fixed 35 percent rate
earns on each curve, and what that fixed rate costs against each
curve's true peak.

## Output

```
demand elasticity, audited: does the demand curve set the peak?
  volume = 1000 x (1 - rate x k); k = elasticity slope
  k = 1.6 reproduces stage 42's executed table

elasticity k | peak rate | peak revenue | revenue at 35% | loss vs peak
    1.2 |     42.0% |      $   208 |       $   203 |       2.6%
    1.6 |     31.0% |      $   156 |       $   154 |       1.4%
    2.0 |     25.0% |      $   125 |       $   105 |      16.0%

reading: the stage's 35% is optimal only on its own curve.
On the sticky market (k=1.2) the peak is 42.0%; on the
elastic one (k=2.0) it is 25.0%, and the fixed 35% earns
$203 vs $105 across the two curves - 48% less revenue with
no change in the rate. The demand curve sets the peak; the
platform prices to the curve it actually has.
```

## Notes

- One declared volume-response family `1000 x (1 - rate x k)`; the
  stage's 1.6 slope is one member, and 1.2 and 2.0 bracket the sticky
  and elastic markets.
- The revenue peak moves with the slope: 42.0 percent on the sticky
  curve, 31.0 percent on the stage's curve, 25.0 percent on the elastic
  one.
- The stage's fixed 35 percent is within 2.6 percent of the peak on the
  curve it was fitted to, but 16.0 percent below the peak on the
  elastic curve; across the two outer curves the same 35 percent rate
  earns \$203 versus \$105, a 48 percent revenue difference with no
  change in the rate.
- The take rate is a price, and the demand curve is the marketplace's
  actual volume response; the sweep demonstrates the shape, real
  take-rate decisions need the measured elasticity of a live
  marketplace.
