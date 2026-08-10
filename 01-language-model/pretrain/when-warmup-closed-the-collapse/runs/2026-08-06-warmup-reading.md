# Run — the warmup contrast: eval spread vs train-loss spread

**Date:** 2026-08-06
**Command:** `uv run python core/warmup_reading.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded warmup JSON).
**Cost:** \$0 (local lane; the underlying training was the stage's recorded
run).

## Purpose

Stage 06 recorded the warmup's eval-spread fall. This run reads the JSON and
lays out the contrast that explains the mechanism: the per-seed eval
scores (collapse closed) versus the per-seed final train loss (still wide).

## Output

```
eval exact-match: warmup mean 0.4970 spread 0.0536 per-seed [0.4707, 0.5242, 0.4962]
stage-01 baseline (no warmup): mean 0.4375 spread 0.2309
final train loss: mean 0.4647 spread 0.2302 per-seed [0.5708, 0.4827, 0.3406]
```

## Notes

- Eval spread fell 0.2309 to 0.0536: the warmup closed the seed-2 eval
  collapse (0.2844 -> 0.4962, now inside the others' band).
- Train-loss spread stayed at 0.2302 — the seeds still end at very
  different training losses. The contrast is the mechanism: the collapse
  was an optimization-path divergence (one seed's LR was too hot early and
  its eval collapsed), not an irreducible seed difference the final loss
  itself would surface. The warmup fixed the path, not the variance.
