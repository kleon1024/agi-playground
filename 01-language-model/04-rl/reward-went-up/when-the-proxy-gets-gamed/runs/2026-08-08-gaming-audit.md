# Run — the proxy that gets gamed, measured across three signals

**Date:** 2026-08-08
**Command:** `uv run python core/gaming_audit.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

The reward-went-up chapter names the inverted U (Gao, Schulman, and
Hilton 2023) and the hacks a reward function makes available; this run
executes the case-finding audit those claims point at. A policy walks a
one-dimensional verbosity parameter under gradient ascent on a proxy
reward whose peak sits past the true quality peak — the reward model's
blind spot over-weighting verbosity. The audit tracks three signals every
step (proxy, held-out true quality, KL from the reference policy) and
samples the policy's output distribution at checkpoints (mean response
length, spurious-keyword rate), because the distribution drift is the
case-finding step that fires before the held-out eval fully collapses.

## Output

```
one-dimensional policy walk: reference theta 0.6, true peak 1.0, proxy peak 1.5
gradient ascent on the proxy only; true quality and KL read as held-out signals

step  theta  proxy  true   KL      proxy/KL  true/KL
   0  0.600  0.190  0.840  0.000       inf       inf
  10  0.765  0.459  0.945  0.014     19.87      7.72
  20  0.899  0.639  0.990  0.045      5.76      1.45
  30  1.009  0.759  1.000  0.084      3.08      0.26  <-- true quality peaks here
  40  1.099  0.839  0.990  0.124      1.97     -0.24
  60  1.232  0.928  0.946  0.200      1.18     -0.59
  80  1.321  0.968  0.897  0.260      0.66     -0.82

distribution check: 500 responses sampled per checkpoint
  step  theta  mean length  keyword rate  true quality
     0  0.600        60.1          6.4%         0.840
    10  0.765        76.8         15.0%         0.945
    20  0.899        89.6         22.4%         0.990
    30  1.009       100.5         24.4%         1.000
    40  1.099       110.9         26.4%         0.990
    60  1.232       123.4         35.6%         0.946
    80  1.321       132.7         42.6%         0.897

verdict: the proxy rises monotonically (0.19 -> 0.97) -- by itself the run
looks like success. The held-out quality peaks at step 30 (theta 1.01) then
falls to 0.90, so the divergence point is the case-finding moment. The
distribution check fires at the same place: the spurious keyword rate and
mean length keep rising monotonically toward the proxy's blind spot, and
the KL tell shows why -- proxy gain per KL unit collapses while true
quality per KL unit goes negative, i.e. the last KL is bought at negative
quality.
```

## Reading the output

- **The proxy alone says success.** It rises monotonically from 0.19 to
  0.97 across the whole walk; a team watching only the training reward
  sees eighty steps of improvement. The divergence is invisible to the
  instrument being optimized.
- **The held-out quality marks the case-finding moment.** True quality
  peaks at step 30 (theta 1.01, quality 1.000) and falls to 0.897 by step
  80 — a ten-point loss bought by the last fifty steps, which the proxy
  reports as gains from 0.759 to 0.968. The divergence step is where the
  disagreement trio (training reward, held-out quality, KL cost) has to be
  read together.
- **The distribution check names the mechanism before the eval collapses.**
  The spurious-keyword rate climbs 6.4% to 42.6% and mean response length
  60 to 133 across the walk; at the divergence step the keyword rate has
  already quadrupled while quality is still at its peak. The policy is
  drifting toward the proxy's blind spot, and the drift is measurable in
  the output distribution before the held-out number turns down.
- **The KL tell prices the trade.** Proxy gain per KL unit collapses from
  19.87 to 0.66 while true quality per KL unit goes from +7.72 to -0.82 —
  the last KL is bought at negative quality. That is the quantitative
  version of "you are burning KL for the scorer's blind spots."
- **Deterministic.** Fixed seed 7; rerunning reproduces the numbers.

## Evidence boundary

This is a mechanism demo, not a trained model: the policy is one
parameter, the proxy and true-quality curves are declared formulas, and
the exact rates (peaks at 1.0 and 1.5, step 30 divergence) do not
transfer. What transfers is the shape of the failure — a proxy that
keeps rising past the true peak, an output distribution drifting toward
the proxy's blind spot, and a KL-per-unit tell that prices the trade —
and the three-signal read that catches it. The real training-scale claims
the README reasons about are cited, dated external results: the inverted
U and its coefficients from Gao, Schulman, and Hilton (arXiv:2210.10760,
2023), reward hacking characterization from Skalse et al.
(arXiv:2211.00694, Nov 2022) and Pan et al. (arXiv:2202.03006, Feb 2022),
and reward-model error rates from RewardBench (Lambert et al.,
arXiv:2403.13787, Mar 2024). No model was trained here.
