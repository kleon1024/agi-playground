# Run: 61 — when gating does not help

- **Command:** `uv run python core/gating_no_help.py` (from
  `02-personalized-discovery/recommendation/61-multi-task-conflict/when-gating-does-not-help/`)
- **Config:** task pair declared to want the same representation; gate
  weight read.
- **Hardware:** local Mac (CPU)
- **Wall-clock:** 0.04s
- **Cost:** \$0
- **Metrics:** task 0 gate 0.99/0.01; task 1 gate 0.98/0.02; effective
  architecture is one expert.
