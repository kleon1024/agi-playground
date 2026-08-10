# Run — when the slice trades, executed on the tail-weight sweep

**Date:** 2026-08-07
**Command:** `uv run python core/slice_trades.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 4.5s (5 weights x 60 epochs).
**Cost:** \$0 (local lane).

## Purpose

Stage 64's slice weighting has a dial: the tail weight. This detour sweeps
the dial from 1.0 to 5.0 and reads what each step buys and sells — tail AUC
up, head AUC down, aggregate AUC nearly flat — to show where the frontier
saturates and why the aggregate metric cannot see the trade.

## Output

```
when the slice trades, read (tail weight sweep):
  tail weight tail auc head auc  agg auc
  1.0            0.654    0.673    0.735
  2.0            0.682    0.638    0.725
  3.0            0.695    0.621    0.717
  4.0            0.702    0.609    0.710
  5.0            0.708    0.602    0.704

reading: the first weight steps buy the tail cheaply and the
aggregate AUC does not move, so a model owner watching only the
aggregate cannot tell whether the tail is being bought or sold.
the frontier saturates as the tail weight keeps rising, and where
to sit is a product trade -- the tail slice's experience against
the head slice's -- that no single model metric decides.
```

## Notes

- The first steps are the cheapest: weight 1.0 to 2.0 buys tail AUC
  +0.028 for head -0.035. From 3.0 up, each step buys less than the
  previous one — the frontier saturates around a tail AUC of 0.71.
- The aggregate AUC falls monotonically (0.735 to 0.704) while the tail
  gains — so the aggregate is not neutral, it is head-weighted. Watching
  it alone misreads a deliberate reallocation as a regression.
- Where to sit is a product decision (tail slice experience versus head
  slice experience), which is why the stage's ownership section puts the
  verdict in front of the product owner, not the model team alone.
