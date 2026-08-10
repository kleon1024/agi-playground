# Run — when the exchange times out, executed on the unfilled-slot model

**Date:** 2026-08-07
**Command:** `uv run python core/exchange_timeout.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 29 runs real-time bidding. This run prices the exchange timeout
rate in unfilled requests on a million-request day.

## Output

```
exchange timeout, read (1,000,000 requests):
  1% timeout: 10,000 requests unfilled
  5% timeout: 50,000 requests unfilled
  10% timeout: 100,000 requests unfilled

reading: every timed-out request is a slot that runs without a
bid — the publisher's inventory, the exchange's revenue, and the
advertiser's reach all miss together. Timeout rate is a revenue
metric, not an availability footnote.
```

## Notes

- A 5% timeout rate leaves 50,000 of a million requests unfilled —
  slots that run without a bid.
- Timeout rate is a revenue metric: the publisher's inventory, the
  exchange's revenue, and the advertiser's reach miss together.
