# Run: 63 — when top-K is not preserved

- **Command:** `uv run python core/topk_not_preserved.py` (from
  `02-personalized-discovery/recommendation/63-cascade-consistency/when-top-k-is-not-preserved/`)
- **Config:** 1,000-item catalogue, click-based cut at 80, final top-20;
  deterministic seed.
- **Hardware:** local Mac (CPU)
- **Wall-clock:** 0.04s
- **Cost:** \$0
- **Metrics:** 11 of the final top-20 survive the cut.
