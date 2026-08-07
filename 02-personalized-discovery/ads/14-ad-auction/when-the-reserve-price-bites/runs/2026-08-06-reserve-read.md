# Run — the reserve price, executed on the stage's auction

**Date:** 2026-08-06
**Command:** `uv run python core/reserve_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Second-price with a single bidder pays the platform zero. This run extends
the auction with a reserve price and shows how it changes allocation and
revenue.

## Output

```
  reserve 0.00: bids [1.00, 0.80] -> winner bidder 0 at 0.80
  reserve 0.70: bids [1.00, 0.80] -> winner bidder 0 at 0.80
  reserve 0.85: bids [1.00, 0.80] -> winner bidder 0 at 0.85
  reserve 0.95: bids [1.00, 0.80] -> winner bidder 0 at 0.95
```

## Notes

- At reserve 0.85 the second bidder is out and the winner pays the
  reserve; the reserve both floors revenue and can kill a sale.
- Setting it is the platform's call — the trade between revenue floor and
  losing low-value sales.
