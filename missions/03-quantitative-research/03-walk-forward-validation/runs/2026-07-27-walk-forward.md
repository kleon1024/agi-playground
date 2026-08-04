# Walk-forward leakage comparison

- Command: `uv run python missions/03-quantitative-research/03-walk-forward-validation/core/walk_forward.py`
- Hardware: local macOS lane
- Software: Python via uv; standard library and stage 00 price fetcher
- Wall-clock: 0.4 seconds
- Cost: \$0 (local lane; public price endpoint)
- Metrics: 1,255 AAPL bars; 1,230 usable five-day labels. A fold-fitted linear rule produced shuffled-invalid out-of-fold Sharpe 0.7393, chronological-unpurged 0.9722, and purged-five-day/gapped-five-day 0.9722; 14-trial teaching deflation was 0.3145. The protected first fold used 605 train and 123 test observations; the chronological paths evaluated 615 test returns.
- Notes: the recovered implementation never used its training indices, so purge could not affect its statistic; this run is from the corrected fold-fitted path. This particular fixed rule still did not exhibit a leakage uplift. That is evidence about this run, not proof that leakage is harmless. Counterfactual widget windows are labelled illustrative.

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
