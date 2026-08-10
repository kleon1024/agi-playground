# Run — the mid-range point, read from the recorded third-endpoint seeds

**Date:** 2026-08-06
**Command:** `uv run python core/midrange_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads six committed seed JSONs).
**Cost:** \$0 (local lane; the training was the stage's recorded 2026-08-01
runs).

## Purpose

Stage 04 picked NR-ER as the mid-range point on the imbalance spectrum.
This run reads the committed seeds and lays out the verdict — the model
wins beyond its own spread — and where that puts the three-point pattern.

## Output

```
NR-ER, third endpoint, read from the recorded seeds:
  descriptor: [0.6411, 0.641, 0.642]  mean 0.6413 spread 0.0011
  model:      [0.6804, 0.6577, 0.6656]  mean 0.6679 spread 0.0227
  gap (model - descriptor): +0.0265  vs larger spread 0.0227
  -> MODEL WINS beyond its own spread
```

## Notes

- NR-ER's model spread (0.0227) sits between SR-MMP's (0.0159) and
  NR-PPAR-gamma's (0.0620), matching its mid-range positive count (12.8%)
  — the scarcity-variance pattern holds with a third point.
- The model wins here, so the winner is not decided by scarcity alone;
  scarcity decides whether a winner can be seen, not which arm wins.
