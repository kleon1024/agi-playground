# Run — the collapse that warmup closed, read from the recorded warmup JSON

**Date:** 2026-08-06
**Command:** `uv run python core/warmup_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the committed JSON).
**Cost:** \$0 (local lane; the training was the stage's recorded 2026-08-02
run).

## Purpose

Stage 06 retrained the vision pathway with a linear LR warmup. This run
reads the recorded JSON and lays out the before/after.

## Output

```
  stage 01: mean 0.4375, spread 0.2309, seeds [0.5128, 0.5153, 0.2844]
  warmup:   mean 0.4970, spread 0.0536, seeds [0.4707, 0.5242, 0.4962]
  warmup config: 10% linear warmup over 186 of 1860 steps
```

## Notes

- The collapse was the seed-2 outlier (0.2844); warmup closed it — spread
  tightens 0.2309 -> 0.0536 and mean rises 0.4375 -> 0.4970.
- The fix is a training-dynamics one: the mechanism is the warmup, not an
  architecture change.
