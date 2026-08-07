# Run — truthful bidding dominance, verified on the stage's auction

**Date:** 2026-08-06
**Command:** `uv run python core/truth_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Stage 14 states second-price makes truthful bidding dominant. This run
verifies it computationally across true values and bids.

## Output

```
  advertiser true value 0.5:
    bid 0.3 -> loses, utility 0.00
    bid 0.5 -> loses, utility 0.00
    bid 1.8 -> wins at 1.00, utility -0.50
  advertiser true value 1.0:
    bid 0.3 -> loses, utility 0.00
    bid 1.0 -> wins at 1.00, utility 0.00
    bid 1.8 -> wins at 1.00, utility 0.00
  advertiser true value 1.5:
    bid 1.5 -> wins at 1.00, utility 0.50
    bid 1.8 -> wins at 1.00, utility 0.50
```

## Notes

- Bidding the true value never yields lower utility than lying —
  underbidding risks losing, overbidding risks paying more than value.
- The dominant strategy is the honest one.
