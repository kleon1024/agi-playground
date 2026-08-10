# Cost and capacity run

- Command: `uv run python 03-quantitative-research/04-cost-and-capacity/core/cost_capacity.py --ticker AAPL --range 2y --turnover 6`
- Hardware: local macOS lane
- Software: Python via uv; standard library; public Yahoo chart endpoint
- Wall-clock: 0.3 seconds
- Cost: \$0 (local lane; public endpoint)
- Metrics: 500 bars; ADV USD 12,578,055,538; daily volatility 1.7839%; assumed Y 0.6, spread 2.0 bps, commission 0.5 bps; at a USD 10m book, 0.0398% participation and 0.2780% annual cost; on the declared 12% paper-return scenario, discrete-sweep peak USD 25,156,111,076 and total-return breakeven USD 125,780,555,379.
- Notes: ADV and volatility are measured inputs. All spread, commission, gross-return, rebalance cadence, and impact assumptions are not fitted execution evidence.

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
