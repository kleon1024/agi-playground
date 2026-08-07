# Run — the one-bidder reserve sweep

**Date:** 2026-08-07
**Command:** `uv run python core/reserve_one_bidder.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.06s.
**Cost:** \$0 (local lane).

## Purpose

The stage audit showed a single-bidder auction pays only the reserve. This
read asks the follow-up: what should the reserve be when the market is
thin? It sweeps the reserve in a one-bidder market over 50,000 draws
(fixed seed) and measures revenue per auction and the sale rate.

## Output

```
thin-market read: one bidder per auction, value ~ U(0,1), 50,000 draws
   reserve   rev/auc  sale rate
      0.00    0.0000     1.0000
      0.20    0.1601     0.8003
      0.30    0.2097     0.6989
      0.40    0.2389     0.5973
      0.50    0.2492     0.4985
      0.60    0.2404     0.4006
      0.70    0.2091     0.2987
      0.90    0.0894     0.0993
```

## Notes

- Revenue per auction peaks at reserve 0.50 (0.2492): the balance point
  between price and sale probability for U(0,1) values. That peak is the
  monopoly reserve the revenue-maximization literature derives (Myerson,
  1981).
- The same reserve's best thin-market outcome (0.25) is far below a deep
  market: four bidders at reserve 0.50 earned 0.6118 per auction in the
  stage audit. Depth beats reserve tuning.
- Values drawn from U(0,1) with a fixed seed; illustrative and
  deterministic, not a real demand distribution.
