# Run — as-of join vs naive join, AAPL Assets across all fiscal periods

**Date:** 2026-08-06
**Command:** `uv run python core/asof_vs_naive.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only (plus the SEC EDGAR
fetch).
**Software:** Python 3.11.14 via uv; reuses the stage's `point_in_time.py`
unmodified.
**Wall-clock:** 0.4s (142 facts fetched).
**Cost:** \$0 (local lane).

## Purpose

Stage 00's recorded run showed one restatement period (2015-06-30). This run
generalizes: scan every fiscal period of AAPL's Assets, compare the naive
join (latest filed value per period) against the point-in-time join (as of
period end + 45 days), and count how often naive is wrong and by how much.

## Output

```
facts fetched: 142 (CIK 789019, Assets)

restatement found: period 2015-06-30 — first filed 2015-07-31
  176,223,000,000, latest filed 2016-07-28 174,472,000,000

fiscal end  naive              as-of (+45d)       gap
2015-06-30  174,472,000,000  176,223,000,000   0.99%
2016-06-30  193,468,000,000  193,694,000,000   0.12%
2017-06-30  250,312,000,000  241,086,000,000   3.83%

recent 6 periods (all as-of == naive)

69 periods total, 3 naive/as-of mismatches (4%), mean |gap| 1.65%
```

## Notes

- Three of 69 fiscal periods (4%) are silently wrong under the naive join,
  with a mean error of 1.65% and a worst case of 3.83% (2017-06-30: the
  naive join returns 250.3B, the value actually knowable 45 days after the
  period end is 241.1B).
- The wrong value is always the LATER restatement — future information a
  backtest has no right to — so the naive join's error is a look-ahead
  violation, not a measurement error.
- The recent six periods all agree: the mechanism is real but episodic, which
  is exactly why the discipline is easy to skip and why "it has not bitten
  recently" is not evidence it cannot bite. The 2017 period is one quarter
  of the book's equity being wrong by 3.8% if joined naively.
