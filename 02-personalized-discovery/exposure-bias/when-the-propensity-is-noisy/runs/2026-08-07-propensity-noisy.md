# Run: 59 — when the propensity is noisy

- **Command:** `uv run python core/noisy_propensity.py` (from
  `02-personalized-discovery/recommendation/59-exposure-bias/when-the-propensity-is-noisy/`)
- **Config:** exact vs noisy propensities vs noisy with cap 20 over a
  synthetic exposure log; deterministic seed.
- **Hardware:** local Mac (CPU)
- **Wall-clock:** 1.17s
- **Cost:** \$0
- **Metrics:** exact: mean w 1.5, max w 4.1, corr 0.980; noisy: 216.6,
  10,000.0, 0.376; capped: 2.6, 20.0, 0.986.
