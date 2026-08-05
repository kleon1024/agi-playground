# Run — SwiGLU vs ReLU vs GELU, output statistics on random inputs

**Date:** 2026-08-06
**Command:** `uv run python core/swiglu_anatomy.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; numpy.
**Wall-clock:** 0.15s (200k draws).
**Cost:** \$0 (local lane).

## Purpose

The 88M decoder's feed-forward block is a SwiGLU. This run measures the
mechanism on random inputs at the repo's geometry: how the hidden-unit
output distribution differs under ReLU, GELU, and SwiGLU.

## Output

```
activation     mean      std  near-zero
ReLU         0.3973   0.5824      50.1%
GELU         0.2804   0.5865       0.2%
SwiGLU      -0.0007   0.5943       0.9%
```

## Notes

- ReLU zeroes half its units (50.1% near-zero on standard-normal input) —
  the dead-neuron regime the plain MLP pays for.
- GELU smooths the bend and removes the dead zone (0.2%).
- SwiGLU's output is zero-mean (-0.0007) with no dead zone: it multiplies
  the gate by a zero-mean up-projection, so the interaction centers the
  signal instead of squashing it — the mechanism, not a learned-weight
  property, is what the run isolates.
- The gate (SiLU) passes negatives through a damped sign-kept transform
  rather than zeroing them (ReLU) or bending them (GELU).
