# Run: 58 — negative sampling

- **Command:** `uv run python core/negative_sampling.py` (from
  `02-personalized-discovery/recommendation/58-negative-sampling/`)
- **Config:** 10x negative downsampling, then the ratio correction; the same
  model trained on the full set, the downsampled set, and the
  downsampled-then-corrected set. Deterministic seed.
- **Hardware:** local Mac (CPU)
- **Wall-clock:** 1.21s
- **Cost:** \$0
- **Metrics:**
  - full set: AUC 0.659, ECE 0.011
  - downsampled: AUC 0.659, ECE 0.473
  - downsampled + corrected: AUC 0.659, ECE 0.017

The full printed read, reproduced verbatim on 2026-08-07:

```text
negative sampling, read (10x downsample, then correct):
  model                 auc     ece
  full set            0.659   0.011
  downsampled         0.659   0.473
  downsampled+corrected  0.659   0.017

reading: downsampling costs almost no ranking (auc holds) while
breaking calibration: the base rate inside the model is 10x the
true one, so every probability inflates. the ratio correction
pulls the probabilities back to the true scale; ranking metrics
alone would never have caught the break.
```
