# Run — the capacity curve across the full book-size range

**Date:** 2026-08-06
**Command:** `uv run python core/capacity_cliff.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only (plus the Yahoo fetch).
**Software:** Python 3.11.14 via uv; reuses the stage's `cost_capacity.py`
unmodified.
**Wall-clock:** 0.2s.
**Cost:** \$0 (local lane).

## Purpose

Stage 04's recorded run reported one point plus the peak and breakeven. This
run sweeps the book across the full log range on the same measured inputs
(AAPL ADV, realized vol) and the same declared assumptions, so the capacity
curve is laid out.

## Output (selected rows)

```
book          participation  annual cost  net pct   net dollar
1,000,000,000       3.93%       1.44%     10.56%     105,627,570
10,000,000,000     39.31%       4.22%      7.78%     777,938,022
31,622,776,602    124.32%       7.39%      4.61%   1,458,221,305
56,234,132,519    221.08%       9.80%      2.20%   1,235,485,984
100,000,000,000   393.14%      13.02%     -1.02%  -1,022,429,996

peak book (max net dollar return): $31.6B
breakeven (net return turns negative): $100.0B
```

## Notes

- Net dollar return peaks at \$31.6B (about \$1.46B/year net) and falls after;
  at \$100B the net return turns negative (-\$1.02B/year). The recorded run's
  discrete-sweep peak was \$25.2B — the log-grid sweep lands near it on the
  same scenario; the difference is the grid.
- The participation rate crosses 100% of daily dollar volume just past the
  peak (124% at \$31.6B): beyond the cliff the book is asking the market to
  trade more than its daily volume, which is the capacity limit made
  physical, not a cost-curve artifact.
- All cost assumptions are the stage's declared ones (spread 2 bps,
  commission 0.5 bps, Y 0.6); ADV and volatility are measured.
