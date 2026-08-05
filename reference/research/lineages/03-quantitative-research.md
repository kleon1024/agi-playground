---
level: reference
---

# The open-source line behind quantitative research

> Dated survey, 2026-08-06. Sources cited inline. External claims are not
> re-measured here; every repository claim cites the run that measured it.

**Question:** a backtest is only as honest as its evaluation harness, and
every guardrail this mission builds — point-in-time data, walk-forward folds,
purge and embargo, deflated Sharpe, cost and capacity — is a point on a line
of methodology that was itself learned from expensive failures. This survey
is that line.

## The evaluation harness

**Sharpe ratio** (Sharpe, 1966) gave strategies a single risk-adjusted
number, and **walk-forward validation** (fitting on a window, testing on the
window immediately after, rolling forward) replaced the single split with a
sequence of them. The tradeoff at this end: walk-forward is honest about
regime change and expensive, because every fold refits.

**Purging and embargo** (Lopez de Prado) close the leak a walk-forward split
still has: financial labels built from overlapping windows make a plain time
split see the future across the boundary, so training examples whose label
window overlaps the test period are removed, and an embargo gap stops
slowly-updating features from leaking backward.

## Multiple testing

The central methodological problem of the field is selection bias: try enough
strategies against one history and a good-looking winner is guaranteed. The
line here runs from classical multiple-testing corrections to the finance
specifics — **Harvey, Liu, and Zhu** (2016, "…and the Cross-Section of
Expected Returns") showed most published factors do not survive a multiple-
testing adjustment, and **Bailey and Lopez de Prado** (2014-2017) built the
**deflated Sharpe ratio** and **PBO** (probability of backtest overfitting)
from the same idea: ask how good the best of N random strategies looks by
chance, and require the candidate to clear that bar.

The repo measures this directly. Its signal stage searched 32 variants,
found an in-sample IC of 0.0947, and the permutation null beat it 95 of 300
times (p = 0.317). The follow-up chapter
[when breadth inflates the winner](../../../missions/03-quantitative-research/01-signal-research/when-breadth-inflates-the-winner/)
measures the same null at 256, 1,024, and 4,096 candidates: the best-of-N IC
under noise rises 0.090 to 0.157, and the 0.0947 winner is beaten by noise
96% of the time at 256 candidates and always at 1,024. That curve is the
deflated-Sharpe idea measured instead of asserted.

## Data honesty

**Survivorship bias** — a universe built from today's constituents hides the
companies that died — and **look-ahead** — fundamentals joined to the wrong
date — are the data line, and the discipline is the same one mission 01
teaches for training corpora: know exactly what was knowable when.

## Costs and capacity

**Almgren-Chriss** (2000) formalized the transaction-cost and market-impact
models the cost line runs on: a strategy is profitable only net of the cost
of trading it, and capacity is where a research-scale signal stops being
implementable. The repo's cost stage reports net-of-cost Sharpe beside gross,
caps position size against traded volume, and measures the gap instead of
dropping it.

## Evidence boundary

Dated and attributed, not measured. The repo anchors — 32 variants, IC
0.0947, permutation p 0.317, the best-of-N curve, purge/embargo folds, the
net-of-cost gap — cite their runs. The line does not settle whether any
published factor is real; it says which harness a claim has to survive.
