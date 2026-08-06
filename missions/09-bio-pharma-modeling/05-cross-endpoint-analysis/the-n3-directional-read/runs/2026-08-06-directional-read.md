# Run — the n=3 directional read, from the recorded cross-endpoint analysis

**Date:** 2026-08-06
**Command:** `uv run python core/directional_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the committed JSON).
**Cost:** \$0 (local lane; the analysis was the stage's recorded run).

## Purpose

Stage 05's three-endpoint pattern has a stated ceiling. This run reads the
recorded JSON and lays out the two directions and the boundary.

## Output

```
  SR-MMP         train+ 689 model spread 0.0159 gap -0.0830 -> descriptor wins
  NR-PPAR-gamma  train+ 118 model spread 0.0620 gap +0.0037 -> inconclusive
  NR-ER          train+ 628 model spread 0.0227 gap +0.0265 -> model wins
  variance vs positives: monotonic decreasing
  gap vs positives: not monotonic
```

## Notes

- Scarcity decides where a winner can be seen (variance monotonic up as
  positives shrink), not who wins (gap not monotonic).
- The pattern is n=3 and directional, which the analysis states as its
  ceiling — no correlation coefficient is computed or implied.
