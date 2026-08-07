# Run: 56 — when the CVR is censored

- **Command:** `uv run python core/cvr_censored.py` (from
  `02-personalized-discovery/recommendation/56-entire-space-funnel/when-the-cvr-is-censored/`)
- **Config:** same pay signal trained on the clicked subset vs the full
  exposure space; deterministic seed.
- **Hardware:** local Mac (CPU)
- **Wall-clock:** 0.47s
- **Cost:** \$0
- **Metrics:** censored head pay AUC 0.448 (232 positives); full-space head
  pay AUC 0.618 (232 positives).
