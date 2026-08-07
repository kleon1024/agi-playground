# Run — when the bid is capped, executed on the risk-dial model

**Date:** 2026-08-07
**Command:** `uv run python core/bid_capped.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 27 bids to a target. This run sweeps the bid cap and reads the
win-and-pay trade across five auctions.

## Output

```
  cap $0.10: wins 3/5, pays $0.30
  cap $0.08: wins 2/5, pays $0.16
  cap $0.06: wins 1/5, pays $0.06

reading: a tighter cap keeps the advertiser out of expensive
auctions but also out of the cheap ones it could have won at
higher bids. The cap is a risk dial: lower average price, lower
reach. Bidding is a budget decision as much as a value one.
```

## Notes

- Lowering the cap from \$0.10 to \$0.06 drops wins from 3/5 to 1/5
  and spend from \$0.30 to \$0.06.
- The cap is a risk dial: lower average price, lower reach — bidding is
  a budget decision as much as a value one.
