# Run — when the bidder is slow, executed on the deadline model

**Date:** 2026-08-07
**Command:** `uv run python core/slow_bidder.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 29 runs real-time bidding under a deadline. This run reads which
bidders make the 100ms cutoff.

## Output

```
slow bidder, read (deadline 100 ms):
  bidder a: 40 ms -> bid in time
  bidder b: 95 ms -> bid in time
  bidder c: 130 ms -> TIMED OUT

reading: bidder c loses the auction not on price but on speed.
The timeout is a selection mechanism: bids that arrive late
cannot win, and a slow bidder is invisible to the exchange no
matter how good its price is. Latency is a bidder's cost of entry.
```

## Notes

- bidder c arrives at 130ms and is timed out, though its price may be
  the best — the deadline selects on speed, not value.
- The timeout makes latency a bidder's cost of entry: a slow bidder is
  invisible to the exchange no matter how good its price is.
