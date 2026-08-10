# Run: 59 — when exploration traffic is thin

- **Command:** `uv run python core/thin_exploration.py` (from
  `02-personalized-discovery/recommendation/59-exposure-bias/when-exploration-traffic-is-thin/`)
- **Config:** 2% exploration over 20,000 rows against a 2,000-item
  catalogue; deterministic seed.
- **Hardware:** local Mac (CPU)
- **Wall-clock:** 0.04s
- **Cost:** \$0
- **Metrics:** 469 distinct items ever seen; 1,531 (76.5%) never exposed.
