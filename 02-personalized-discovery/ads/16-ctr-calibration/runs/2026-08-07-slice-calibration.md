# Run — the hidden-slice calibration audit

**Date:** 2026-08-07
**Command:** `uv run python core/slice_calibration.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.19s.
**Cost:** \$0 (local lane).

## Purpose

The stage run measures ECE on ten impressions. The audit asks the
case-finding question at production scale: which slices carry the
calibration error? It draws 20,000 impressions (fixed seed) — 18,000 on
a calibrated desktop slice, 2,000 on a mobile slice whose click rate is
half the prediction — and reports aggregate and per-slice ECE.

## Output

```
hidden-slice audit: 20,000 impressions, fixed seed
desktop slice: calibrated (click rate = prediction)
mobile slice:  click rate = half the prediction

     slice   share      ECE  mean pred  mean obs
   desktop   90.0%   0.0042     0.5003    0.4994
    mobile   10.0%   0.2303     0.4983    0.2680
  aggregate    100%   0.0238     0.5001    0.4763
```

## Notes

- The aggregate ECE is 0.0238 — below a typical 0.05 alert bar, so a
  global monitor passes. The mobile slice is 0.2303: its clicks run at
  0.268 against a mean prediction of 0.498, an overestimate of nearly
  half that eCPM ranking, the auction, and budget pacing all consume.
- The dilution is arithmetic: a 90 percent well-calibrated majority
  hides a 10 percent broken slice. Stratifying by slice is how the case
  is found, and per-slice monitoring needs enough impressions per slice
  to detect the gap — a small slice needs a longer window.
- Predictions drawn from U(0.1, 0.9) with a fixed seed; clicks drawn as
  Bernoulli(rate). Illustrative and deterministic, not real click logs.
