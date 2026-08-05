# Run — the scarcity hypothesis, read from the cross-endpoint analysis

**Date:** 2026-08-06
**Command:** `uv run python core/scarcity_grid.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded JSON).
**Cost:** \$0 (local lane; the underlying training was the mission's recorded
runs).

## Purpose

Stage 05's recorded analysis checked two directions across the three
endpoints: model variance vs positive count, and the win/loss gap vs
positive count. This run lays both out.

## Output

```
endpoint        train+  model spread      gap  verdict
SR-MMP             689        0.0159  -0.0830  descriptor wins beyond spread
NR-PPAR-gamma      118        0.0620  +0.0037  inconclusive (gap inside spread)
NR-ER              628        0.0227  +0.0265  model wins beyond spread

variance vs positive count: monotonic decreasing
gap vs positive count: not monotonic
```

## Notes

- The scarcity hypothesis holds for variance: the fewest positives (PPAR,
  118) carry the largest model spread (0.062), and the most (SR-MMP, 689)
  the smallest (0.016). Monotonic decreasing, per the recorded direction.
- The gap does not follow scarcity: PPAR's gap is inside its spread
  (inconclusive) while SR-MMP and NR-ER both resolve, one each way. The
  hypothesis explains where a winner can be SEEN, not who wins — the
  monotonicity check is n=3, direction only, no correlation implied.
