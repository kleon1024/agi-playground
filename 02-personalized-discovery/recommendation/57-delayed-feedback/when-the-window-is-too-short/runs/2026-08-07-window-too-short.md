# Run: 57 — when the window is too short

- **Command:** `uv run python core/window_too_short.py` (from
  `02-personalized-discovery/recommendation/57-delayed-feedback/when-the-window-is-too-short/`)
- **Config:** label-window sweep (1/3/7/14/30 days) over the same synthetic
  conversion stream; deterministic seed.
- **Hardware:** local Mac (CPU)
- **Wall-clock:** 0.95s
- **Cost:** \$0
- **Metrics:** conv AUC by window: 0.462 / 0.695 / 0.705 / 0.690 / 0.702;
  false negatives 728 / 421 / 122 / 11 / 0; train rows 4,754 / 4,498 /
  4,001 / 3,112 / 1,217.
