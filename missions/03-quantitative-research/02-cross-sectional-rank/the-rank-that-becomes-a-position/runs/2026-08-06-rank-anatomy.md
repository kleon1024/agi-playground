# Run — the rank-to-position anatomy, read from the recorded stage-02 run

**Date:** 2026-08-06
**Command:** `uv run python core/rank_anatomy.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the ranking was the stage's recorded 2026-07-27
run).

## Purpose

The cross-sectional rank model is a pipeline — signal, rank, weight,
position — and the sizing rule is where the strategy lives. This run reads
the recorded stage-02 run and lays out the four rules it measured on the
same signal family.

## Output

```
cross-sectional rank anatomy (recorded stage-02 run), read:
  rule                     HHI  turnover  Sharpe  constrained gross  violations
  Equal-weight decile   0.6667     0.638   -0.68
  Rank-proportional     0.1776     0.348   -1.05
  Signal-proportional   0.2243     0.369   -1.20
  Volatility-scaled     0.1952     0.404   -0.83
  cap violations: ['7', '47', '35', '43']
```

## Notes

- The signal is fixed and the rule changes the portfolio: equal-weight
  concentrates on the tails (HHI 0.6667), rank-proportional spreads across
  the full order (HHI 0.1776).
- Every rule breaks the cap after naive cap-then-sector-de-mean (7 to 47
  violations), which is why a joint constrained optimizer is necessary.
- The Sharpe values are cost-free, capacity-free paper diagnostics on a
  30-name panel — an upper bound for sizing mechanics, not live evidence.
