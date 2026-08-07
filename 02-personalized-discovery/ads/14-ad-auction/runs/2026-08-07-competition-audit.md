# Run — the competition-stratified revenue audit

**Date:** 2026-08-07
**Command:** `uv run python core/competing_auctions.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.06s.
**Cost:** \$0 (local lane).

## Purpose

The stage run shows one second-price auction. The audit asks the
case-finding question: where does the platform's revenue actually come
from? It sweeps the number of bidders per auction over 20,000 auctions
per count (fixed seed) and reports revenue per auction, the sale rate,
the share of sales that pay exactly the reserve, and the average top
bid. A market that thins is the failure mode behind "fill is up but
revenue per auction is down."

## Output

```
competition audit: 20,000 auctions per bidder count, values ~ U(0,1)
reserve 0.50; revenue per auction and where it comes from

   bidders   rev/auc  sale rate reserve-bound top-bid avg
         1    0.2514     0.5027        1.0000      0.5010
         2    0.4140     0.7467        0.6687      0.6652
         3    0.5311     0.8753        0.4318      0.7509
         4    0.6118     0.9355        0.2668      0.7996
         8    0.7776     0.9966        0.0310      0.8888
```

## Notes

- Revenue per auction rises with bidder count: 0.2514 (one bidder) to
  0.6118 (four) to 0.7776 (eight). Thinning the market from four
  bidders to one cuts revenue per auction by about 59 percent.
- The reserve-binding share is the diagnostic: with one bidder every
  sale pays the 0.50 floor (100 percent); with eight bidders only 3.1
  percent of sales touch the reserve, and competition sets the price.
- Values drawn from U(0,1) with a fixed seed; illustrative and
  deterministic, not a real demand distribution.
