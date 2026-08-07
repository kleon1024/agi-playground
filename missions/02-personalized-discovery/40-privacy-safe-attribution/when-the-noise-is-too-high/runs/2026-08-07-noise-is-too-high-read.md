# Run — when the noise is too high, executed on the collapse-point read

**Date:** 2026-08-07
**Command:** `uv run python core/noise_collapse.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 40 adds DP noise to attribution. This run sweeps epsilon and reads where the channel order breaks.

## Output

```
noise collapse, read:
  epsilon 5.0: noisy [485, 308, 263], rank ['search', 'display', 'email'], order preserved True
  epsilon 2.0: noisy [470, 330, 265], rank ['search', 'display', 'email'], order preserved True
  epsilon 0.5: noisy [450, 230, 350], rank ['search', 'email', 'display'], order preserved False

reading: at epsilon 5 the order survives; at 0.5 it collapses.
The privacy guarantee and the decision accuracy are the same
dial — epsilon is chosen so the noisiest plausible draw still
keeps the budget decision intact.
```

## Notes

- At epsilon 5 the order survives; at 0.5 the noise reorders email above display and the budget decision breaks.
- The privacy guarantee and the decision accuracy are the same dial — epsilon is chosen so the noisiest plausible draw still keeps the budget decision intact.
