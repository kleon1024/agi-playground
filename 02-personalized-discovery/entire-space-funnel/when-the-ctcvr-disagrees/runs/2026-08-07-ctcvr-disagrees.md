# Run: 56 — when the CTCVR disagrees

- **Command:** `uv run python core/ctcvr_disagrees.py` (from
  `02-personalized-discovery/recommendation/56-entire-space-funnel/when-the-ctcvr-disagrees/`)
- **Config:** three declared impressions (cold head 2% CTR, mid funnel 10%,
  strong intent 30%) with noisy CTCVR reads.
- **Hardware:** local Mac (CPU)
- **Wall-clock:** 0.04s
- **Cost:** \$0
- **Metrics:** derived p_pay 0.020 / 0.120 / 0.100 raw; clipping keeps
  p_pay <= p_click in every row.
