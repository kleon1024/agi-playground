# Run — privacy-safe attribution, executed on the DP-noise budget model

**Date:** 2026-08-07
**Command:** `uv run python core/dp_attribution.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 40 asks how attribution survives differential privacy. This run adds Laplace noise to channel counts and reads the resulting rank.

## Output

```
privacy-safe attribution, read (epsilon 2.0):
  search: true 480, noisy 462
  display: true 310, noisy 275
  email: true 260, noisy 275
  true rank:  ['search', 'display', 'email']
  noisy rank: ['search', 'email', 'display']
  order preserved: False

reading: the noise hides any individual's contribution, but it
can reorder the channels that decide budget. Epsilon trades
privacy against decision accuracy — the noise-too-high detour
shows the collapse point.
```

## Notes

- The noise hides any individual's contribution, but it can reorder the channels that decide budget.
- Epsilon trades privacy against decision accuracy — the noise-too-high detour shows the collapse point.
