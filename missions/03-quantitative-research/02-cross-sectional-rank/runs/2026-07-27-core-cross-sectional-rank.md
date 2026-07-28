# Run — stage 02 cross-sectional ranking

**Date:** 2026-07-27
**Command:** `uv run python core/cross_sectional_rank.py --range 3y --top-frac 0.1 --cap 0.10`
**Hardware:** Apple arm64 local machine, CPU-only.
**Software:** Python managed by uv; standard-library core and Yahoo Finance's
public chart endpoint.
**Wall-clock:** 4.43 seconds.
**Cost:** $0 (local lane).

## Metrics

The script fetched 30 names with 752 common trading days, producing 24 usable
month-end rebalances from 2024-07-31 to 2026-06-30. Every raw sizing rule began
at gross 2.00. Its mean raw HHI / monthly turnover / paper Sharpe were:

| Rule | HHI | Turnover | Paper Sharpe |
|---|---:|---:|---:|
| Equal-weight decile | 0.6667 | 0.638 | -0.68 |
| Rank-proportional | 0.1776 | 0.348 | -1.05 |
| Signal-proportional | 0.2243 | 0.369 | -1.20 |
| Volatility-scaled | 0.1952 | 0.404 | -0.83 |

After naïve cap then sector de-mean, gross exposure was 0.16, 1.32, 1.21, and
1.21 respectively. The procedure left 7, 47, 35, and 43 positions above the
cap, demonstrating why a joint constrained optimizer is necessary.

## Notes

These are cost-free, capacity-free paper results on a small public-data panel.
They are an upper-bound diagnostic for sizing mechanics, not investment advice
or live-performance evidence. The fixed 10% cap and decile fraction were
declared command inputs, not tuned by a parameter search.

## Reproducing this

The command fetches a trailing window from a live public endpoint, so the
window it returns is anchored to the day it runs, not to the date above.
Re-running it later pulls newer bars, drops the oldest ones, and produces
numbers close to but not identical with these. That is a property of the
data source, not a defect in the script: re-running it the next day already
moved this stage's figures in the fourth significant digit. Treat the values
recorded here as this window's result. To compare two methods, run both
against the same fetch rather than against two run records written on
different days.
