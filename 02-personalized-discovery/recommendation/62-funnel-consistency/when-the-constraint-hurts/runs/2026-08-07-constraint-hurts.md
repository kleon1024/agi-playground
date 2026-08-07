# Run: 62 — when the constraint hurts

- **Command:** `uv run python core/constraint_hurts.py` (from
  `02-personalized-discovery/recommendation/62-funnel-consistency/when-the-constraint-hurts/`)
- **Config:** independent order model vs chained read over bad and
  calibrated click heads.
- **Hardware:** local Mac (CPU)
- **Wall-clock:** 0.04s
- **Cost:** \$0
- **Metrics:** independent p(order) 0.12; chained bad 0.27 (2.25x too
  high); chained calibrated 0.12 (correct).
