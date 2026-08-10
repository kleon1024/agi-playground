# Run: 57 — when freshness fights correctness

- **Command:** `uv run python core/freshness_fights.py` (from
  `02-personalized-discovery/recommendation/57-delayed-feedback/when-freshness-fights-correctness/`)
- **Config:** fresh snapshot (0.3-2d), naive vs corrected (remaining-mass
  reweight); deterministic seed.
- **Hardware:** local Mac (CPU)
- **Wall-clock:** 0.56s
- **Cost:** \$0
- **Metrics:** naive conv AUC 0.712; corrected 0.732; 733 in-flight
  converters in the training rows.
