# Run — when the shading is wrong, executed on the error-cost read

**Date:** 2026-08-07
**Command:** `uv run python core/wrong_shading.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 39's bidder shades its bid. This run compares under-shading, optimal, and over-shading bids.

## Output

```
wrong shading, read (value $1.00, optimum bid $0.50):
  under-shade (bid $0.80): win 0.80, net $0.16
  optimal (bid $0.50): win 0.50, net $0.25
  over-shade (bid $0.20): win 0.20, net $0.16

reading: under-shading wins more but pays too much; over-
shading keeps more margin but loses auctions. Both lose to
the optimum — the shading estimate's error is a direct cost,
which is why first-price bidding is an estimation problem.
```

## Notes

- Under-shading wins more but pays too much; over-shading keeps more margin but loses auctions; both lose to the optimum.
- The shading estimate's error is a direct cost — first-price bidding is an estimation problem.
