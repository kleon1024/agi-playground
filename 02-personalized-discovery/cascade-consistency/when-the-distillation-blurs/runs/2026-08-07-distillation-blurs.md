# Run: 63 — when the distillation blurs

- **Command:** `uv run python core/distillation_blurs.py` (from
  `02-personalized-discovery/recommendation/63-cascade-consistency/when-the-distillation-blurs/`)
- **Config:** clean vs noisy teacher scores distilled into the same
  pre-rank; deterministic seed.
- **Hardware:** local Mac (CPU)
- **Wall-clock:** 0.16s
- **Cost:** \$0
- **Metrics:** distilled rank corr: clean teacher 0.998, noisy teacher
  0.989.
