# Run — the 2x2 factorial across three seeds, read from the recorded JSONs

**Date:** 2026-08-06
**Command:** `uv run python core/factorial_grid.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads three recorded JSONs).
**Cost:** \$0 (local lane; the underlying training was the stage's recorded
run).

## Purpose

Stage 06 crossed dead-code reset with the EMA codebook update. This run
reads the three seeds' four arms and the recorded main effects, so "which
half of the fix did it" is a grid.

## Output

```
arm          seed0 MSE seed1 MSE seed2 MSE
plain        0.0271 0.0170 0.0212
reset-only   0.0187 0.0172 0.0173
ema-only     0.0283 0.0275 0.0275
reset+ema    0.0181 0.0168 0.0205

main effects (seed 0, recorded):
  reset without EMA: -0.0084 MSE, +46 codes
  EMA without reset: +0.0012 MSE, -17 codes
```

## Notes

- Reset is the mechanism that did the work: reset-only beats plain in two
  seeds and ties the healthy third; EMA-only is worse than plain in all
  three seeds (the recorded main effect: -17 codes, worse MSE).
- EMA only helps when the reset is present: reset+ema is the best corner
  (0.0181/0.0168/0.0205), marginally ahead of reset-only — the EMA is an
  enhancer on top of the reset, not a fixer on its own.
- The 2x2 answer is therefore unambiguous across seeds: without the reset,
  EMA alone makes the codebook worse; the reset carried the work.
