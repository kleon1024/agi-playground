# Run — when the surrogate label bleeds, executed on the engaged-proxy read

**Date:** 2026-08-07
**Command:** `uv run python core/surrogate_bleed.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 6.3s (2 variants x 60 epochs).
**Cost:** \$0 (local lane).

## Purpose

Stage 65's surrogate variant uses "engaged" as a stand-in for purchase.
This detour measures the price: a model trained on the surrogate learns
the surrogate's rate, so its predicted purchase probability is inflated
and, judged on the labels that matter, its true-label AUC is worse.

## Output

```
when the surrogate label bleeds, read (cold slices):
  model               true-label buy auc
  true labels                      0.756
  surrogate labels                 0.706
  surrogate mean predicted buy rate on cold items: 0.0395
  true buy rate on cold items: 0.0036

reading: the surrogate fills the empty slice -- engaged is
several times more frequent than purchase -- but the model
trained on it reads 'engaged' everywhere and over-predicts
purchase by the ratio above. on the labels that matter its
true-label AUC is the worse of the two. a surrogate buys
signal and sells probability meaning; the value tree (stage 05)
multiplies that inflated number into every downstream decision.
```

## Notes

- The surrogate fills the empty slice (0.706 true-label AUC is usable
  ranking) but the model trained on it predicts a 0.0395 purchase rate
  against a true 0.0036 — about 11x inflation. A calibrated pCVR would
  read the same; the surrogate's noise is in every predicted probability.
- On the labels that matter its true-label AUC (0.706) is worse than the
  true-label model's (0.756): the surrogate buys signal and sells
  probability meaning.
- The inflated number propagates into the value tree (stage 05), which
  multiplies it into every downstream decision — the same shape as
  fake-negative correction in delayed feedback (Ktena et al., RecSys
  2019; Yasui et al., arXiv:2002.02068, CIKM 2020), where the fix is a
  weighting and a calibration repair, not the label alone.
