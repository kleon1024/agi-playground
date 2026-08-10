# Run: 60 — when the whale dominates

- **Command:** `uv run python core/whale_dominates.py` (from
  `02-personalized-discovery/recommendation/60-heavy-tail-objective/when-the-whale-dominates/`)
- **Config:** synthetic order distribution; gradient-share read under raw
  MSE vs log amount.
- **Hardware:** local Mac (CPU)
- **Wall-clock:** 0.08s
- **Cost:** \$0
- **Metrics:** top 1% gradient share: raw MSE 25.4%, log amount 3.3%.
