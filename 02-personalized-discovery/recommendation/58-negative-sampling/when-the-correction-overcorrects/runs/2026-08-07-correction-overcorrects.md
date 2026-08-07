# Run: 58 — when the correction overcorrects

- **Command:** `uv run python core/correction_overcorrects.py` (from
  `02-personalized-discovery/recommendation/58-negative-sampling/when-the-correction-overcorrects/`)
- **Config:** correction applied with exact, too-low, and too-high assumed
  sampling ratios; deterministic seed.
- **Hardware:** local Mac (CPU)
- **Wall-clock:** 0.09s
- **Cost:** \$0
- **Metrics:** corrected p and bias vs true: exact 0.003/-0.002; too low
  0.002/-0.003; too high 0.005/0.000.
