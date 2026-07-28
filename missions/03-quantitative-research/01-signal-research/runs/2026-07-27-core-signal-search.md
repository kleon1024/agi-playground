# Run — stage 01 signal search

**Date:** 2026-07-27
**Command:** `uv run python core/signal_search.py --range 5y --permutations 300`
**Hardware:** Apple arm64 local machine, CPU-only.
**Software:** Python managed by uv; standard-library core plus the stage 00
Yahoo Finance and SEC EDGAR HTTP clients.
**Wall-clock:** 16.53 seconds.
**Cost:** $0 (local lane).

## Metrics

The ten-name universe fetched completely. It shared 60 monthly rebalance dates
from 2021-07-31 through 2026-06-30. The harness evaluated and logged 32 real
candidate variants: 18 momentum, five low-volatility, and nine value variants.
The best in-sample IC was 0.0947 for momentum with 24-month lookback and no
skip, across 35 scoreable dates and 350 observations.

Across 300 seeded within-date forward-return permutations, the best-of-grid IC
was mean 0.0818, minimum 0.0061, median 0.0794, and maximum 0.2369. Ninety-five
of 300 null searches matched or exceeded the real-data winner, yielding a
permutation p-value of 0.317.

## Notes

The log has 32 JSONL lines, one for every real candidate. Permutation draws are
not research candidates and are intentionally excluded from that count. This is
a small, survivorship-limited public-data exercise; it is a demonstration of
search accounting, not investment evidence.

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
