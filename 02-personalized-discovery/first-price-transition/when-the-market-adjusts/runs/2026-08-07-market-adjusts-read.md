# Run — when the market adjusts, executed on the learning-curve read

**Date:** 2026-08-07
**Command:** `uv run python core/market_adjust.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 39's first-price transition changes bidder behavior. This run reads platform revenue as bidders learn to shade.

## Output

```
market adjustment, read:
  naive (bid full value): shading 1.00, revenue $0.95
  transition (learn shading): shading 0.70, revenue $0.68
  settled (shade to optimum): shading 0.50, revenue $0.42

reading: as bidders learn to shade, the platform's revenue
per auction falls — the first-price transition moved revenue
from the platform to the advertisers over time. A revenue
forecast that assumes naive bidding overstates the steady state.
```

## Notes

- As bidders learn to shade, revenue per auction falls from \$0.95 to \$0.42 — the transition moved revenue from the platform to the advertisers over time.
- A revenue forecast that assumes naive bidding overstates the steady state.
