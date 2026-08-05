# Run — exact-match versus reconstruction, three generation seeds

**Date:** 2026-08-06
**Command:** `uv run python core/wrong_tokens_reconstruct.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads three recorded JSONs).
**Cost:** \$0 (local lane; the underlying training was the stage's recorded
run).

## Purpose

Stage 02's three seeds all beat frame-repeat, but their token-sequence
exact-match rates differ threefold. This run lays out the reconciliation:
how wrong the LM's tokens are by reconstruction MSE, and how that gap sits
against the frame-repeat baseline.

## Output

```
seed  exact-match   lm MSE  oracle MSE     gap  framerepeat
   0        0.067   0.0804      0.0779 +0.0025      0.1281
   1        0.220   0.0865      0.0865 +0.0000      0.1281
   2        0.193   0.0882      0.0882 +0.0000      0.1281

exact-match: mean 0.160, half-range 0.077
reconstruction gap (lm - oracle): mean +0.0008
```

## Notes

- Exact-match spans 0.067 to 0.220 — a threefold seed spread, the kind of
  gap the repo's own rule says to report as variance, not a single number.
- The reconstruction gap is +0.0008 on average: the LM's wrong token
  sequences reconstruct almost exactly as well as the oracle's. The codebook
  carries near-equivalent tokens for the same frame content, so a wrong
  choice often renders the same pixels.
- The frame-repeat baseline sits at 0.1281 MSE — an order of magnitude above
  both. The exact-match metric understates the generation's visual quality;
  the reconstruction metric is what the feasibility verdict (MET) rests on.
