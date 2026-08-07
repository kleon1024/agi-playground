# Run: 62 — when the order exceeds the click

- **Command:** `uv run python core/order_exceeds_click.py` (from
  `02-personalized-discovery/recommendation/62-funnel-consistency/when-the-order-exceeds-the-click/`)
- **Config:** three declared head outputs (strong-intent, cold lead, normal
  item).
- **Hardware:** local Mac (CPU)
- **Wall-clock:** 0.04s
- **Cost:** \$0
- **Metrics:** p(order) > p(click) on 2 of 3 samples; the third is
  consistent.
