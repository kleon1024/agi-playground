# Run — RoPE mechanics on the repo's head geometry

**Date:** 2026-08-06
**Command:** `uv run --group torch python core/rope_attention.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; numpy.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

The 88M decoder uses RoPE at `rope_theta = 10_000`, d_head 64. This run
measures the three properties the chapter teaches, at that geometry: the
translational invariance (score depends only on delta), the wavelength per
dimension, and the fixed-pair score trajectory under two thetas.

## Output

```
d_head=64, rope_theta=10k (the repo's config)

1. translational invariance: same delta, far-apart positions
  delta 3 at (5,2):     -0.100784
  delta 3 at (100,97):  -0.100784
  delta 3 at (1000,997): -0.100784

2. wavelengths per dimension (positions per full rotation)
 dim    theta=10k   theta=500k
   0          6.3          6.3
   8         62.8        167.1
  16        628.3       4442.9
  24       6283.2     118142.8
  31      47117.2    2084764.8

3. fixed-pair score vs delta 1..64
  theta=10k:  mean|score| 0.1359, lag-1 autocorrelation 0.0234
  theta=500k: mean|score| 0.0945, lag-1 autocorrelation 0.0119
```

## Notes

- Translational invariance holds to machine precision across positions 0 to
  1,000: the score for delta 3 is -0.100784 at every absolute position. This
  is the property absolute position embeddings do not give you.
- Dim 0 rotates at exactly one radian per position regardless of theta
  (theta^0 = 1); theta stretches every other dimension's wavelength, most
  dramatically at the top (dim 31: 47,117 positions per cycle at 10k versus
  2,084,765 at 500k). That is why rope_theta is the long-context knob.
- The fixed-pair trajectory is measured on the run's own (q, k) pair; the
  widget recomputes the same curve for any theta from the embedded vectors.
  An average over random pairs would be flat (orthogonal rotation preserves
  an isotropic inner product distribution), which is why the trajectory is
  the right statistic, not the mean.
