# Run: 59 — exposure bias

- **Command:** `uv run python core/exposure_bias.py` (from
  `02-personalized-discovery/recommendation/59-exposure-bias/`)
- **Config:** confounded exposure log (old model's scores drive which items
  get shown); naive logistic on the log vs inverse-propensity-weighted (IPS)
  fit vs random-exposure gold reference. Deterministic seed.
- **Hardware:** local Mac (CPU)
- **Wall-clock:** 3.31s
- **Cost:** \$0
- **Metrics:** quality-rank correlation: naive on log 0.874, propensity (IPS)
  0.962, random exposure 0.995.

The full printed read, reproduced verbatim on 2026-08-07:

```text
exposure bias, read (confounded exposure vs correction):
  model          quality rank corr
  naive on log               0.874
  propensity (IPS)             0.962
  random exposure             0.995

reading: the naive model inherits the old model's exposure, so it
learns 'shown often' more than 'liked'. weighting each logged row
by the inverse exposure propensity removes most of the confound;
random-exposure traffic is the gold reference it is compared to,
and why exploration traffic is worth real money.
```
