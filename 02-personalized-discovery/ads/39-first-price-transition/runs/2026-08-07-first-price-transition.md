# Run — first-price transition, executed on the shading model

**Date:** 2026-08-07
**Command:** `uv run python core/first_price_bid.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 39 asks how to bid when the winner pays its own bid. This run sweeps the bid factor and reads net value.

## Output

```
  factor 1.00: bid $1.00, win 1.00, net $0.00
  factor 0.80: bid $0.80, win 0.80, net $0.16
  factor 0.60: bid $0.60, win 0.60, net $0.24
  factor 0.50: bid $0.50, win 0.50, net $0.25
  factor 0.40: bid $0.40, win 0.40, net $0.24

reading: the winner pays its own bid, so net is (value - bid)
times win probability. With a uniform competitor the optimum is
half the value: bidding $1.00 nets $0.00, bidding $0.50 nets
$0.25. Shade too little and you overpay; too much and you lose
auctions you should have won — the detours price both.
```

## Notes

- The winner pays its own bid, so net is (value - bid) times win probability.
- With a uniform competitor the optimum is half the value: bidding \$1.00 nets \$0.00, bidding \$0.50 nets \$0.25.
