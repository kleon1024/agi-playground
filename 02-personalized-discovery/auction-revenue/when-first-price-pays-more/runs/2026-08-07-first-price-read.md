# Run — when first price pays more, executed on the shading model

**Date:** 2026-08-07
**Command:** `uv run python core/first_price_more.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 28 compares auction rules. This run reads the revenue gap between
first and second price under naive and shaded bidders.

## Output

```
  naive bidders: first $1.20, second $1.00, gap $0.20
  shaded bidders: first $0.96, second $0.80, gap $0.16

reading: first price pays more when bidders bid truthfully and
less when they shade. The revenue rule and the bidder population
are coupled — a revenue comparison is only valid for the bidding
behavior it assumes.
```

## Notes

- Under naive bidding first price pays \$1.20 versus \$1.00, a \$0.20
  gap; under shaded bidding the gap shrinks to \$0.16.
- The revenue rule and the bidder population are coupled — a revenue
  comparison is only valid for the bidding behavior it assumes.
