# Run — the ad auction, executed on the stage's second-price mechanism

**Date:** 2026-08-06
**Command:** `uv run python core/ad_auction.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Ads compete for the same slots as organic results, and the allocation is
an auction. This run executes the second-price mechanism over three
scenarios.

## Output

```
  two bidders    bids [1.0, 0.8] -> winner bidder 0 at 0.80
  three bidders  bids [1.2, 1.0, 0.6] -> winner bidder 0 at 1.00
  one bidder     bids [0.9] -> winner bidder 0 at 0.00
```

## Notes

- The winner pays the second-highest bid, not their own — truthful
  bidding is the dominant strategy, because the bid sets the chance of
  winning while the second bid sets the price.
