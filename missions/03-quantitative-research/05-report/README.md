---
status: verified
verified: 2026-07-27
---

# Can this mission claim anything at all?

Every earlier stage was allowed to fail safely. This one decides whether the
mission gets to claim anything at all, using a contract written before the
code. The contract is [`mission.yaml`](../mission.yaml): two post-cost
baselines, one primary metric, six veto guardrails, measured latency and cost,
and a mandatory regime-level failure record. This chapter does not paraphrase
those requirements into a more flattering score. It turns them into a report
artifact that either produces **MET**, **NOT MET**, or **CANNOT DETERMINE**.

The honest current answer is cannot determine. Stages `01-signal-research`,
`02-cross-sectional-rank`, `03-walk-forward-validation`, and
`04-cost-and-capacity` have implementations, but no integrated mission outcome
artifact. The core report was run against the path where that artifact would
exist and named 18 missing inputs: fold-level candidate and baseline Sharpes,
net and gross results, deflated Sharpe and its trial count, drawdown, capacity,
point-in-time and survivorship checks, cost, latency, and regimes. The real
current-state output is recorded in
[`runs/2026-07-27-report-refusal.md`](runs/2026-07-27-report-refusal.md).

That refusal is the chapter’s artifact. It is the same discipline taught by
`platform/data/01-ablation-harness`: an experiment with missing inputs does
not get a plausible conclusion merely because the missing values would be
inconvenient. A blank report is not conservative; a verdict drawn from it is
wrong.

## Which baseline has to be beaten?

The contract declares two. Buy-and-hold of the same equal-weight universe is a
passive floor. Clearing it establishes activity, not worth: a strategy that
adds trading and complexity ought to beat doing almost nothing. The important
baseline is the published 12-month return, skipping one month,
cross-sectional-momentum heuristic, costed the same way as the candidate.
Momentum is the field’s popularity baseline. It is hard to beat net of costs,
so beating only buy-and-hold cannot establish a new edge.

The primary metric is annualized net-of-cost Sharpe on at least five purged,
embargoed walk-forward folds, reported as a mean and standard deviation. The
candidate must beat **both** baselines by more than fold-to-fold standard
deviation. The report therefore renders both comparisons side by side. A
single aggregate winner and a single fold are not substitutes for this test.

## Why guardrails get a veto

Guardrails are not bonus points. The contract says a strategy profitable only
before costs fails outright; each name must stay within 5% of trailing 20-day
average dollar volume; maximum drawdown cannot exceed 1.5 times passive
drawdown; deflated Sharpe must remain positive at a stated significance level;
point-in-time checks must have zero violations; and the universe must include
every historical member, not today’s survivors. One failure makes the verdict
NOT MET even when returns look impressive.

The core report prints the quoted requirement, threshold, measured input, and
pass/fail state. Its declared 95% significance bar is intentionally explicit:
the mission requires a stated level but does not name one, so hiding a choice
inside formatting would recreate the post-hoc tuning the mission exists to
prevent. It also prints gross beside net rather than allowing gross Sharpe to
substitute for a cost-aware result.

Two complete JSON fixtures exercise the two determinate branches. They are
hand-authored synthetic test data, clearly marked as such, not backtests and
not outcomes. One returns MET; the other clears both baseline comparisons but
fails the deflated-Sharpe guardrail and returns NOT MET. That difference is the
reason for veto-shaped reporting: a reader cannot accidentally interpret a
good headline number as approval. The only measured conclusion for the actual
mission is CANNOT DETERMINE.

## Which period made the aggregate misleading?

An aggregate Sharpe averages across regimes where a strategy behaved
differently. It is often the least informative number in the report. The
artifact requires named periods, dates, candidate Sharpe, momentum Sharpe, and
buy-and-hold Sharpe; it marks the worst candidate regime and prints drawdown
start, trough, and recovery dates. A strategy can have a respectable decade
average because one friendly regime overwhelms a sharp failure in the regime
that matters most to risk. A report that hides this section is hiding the
decision-relevant evidence.

<!-- interactive: RegimeBreakdown -->

The widget is an explicitly illustrative series, not a recorded run. Switch
regimes and watch an acceptable aggregate resolve into a bad volatility-shock
period. In the actual report, that interaction must be backed by the supplied
return series and the recorded regime labels; it cannot be filled with a
generic chart.

Run `uv run python core/report.py` for current state. Use the two files under
`core/fixtures/` only to test the verdict branches. `prod/tearsheet.py` shows
a production reporting boundary: QuantStats, pyfolio/empyrical, or a
hand-rolled metrics-store report are viable alternatives, but none may bypass
the contract evaluator.

## What a passing report would still not promote

The mission contract deliberately refuses to promote a new reusable capability
from one mission alone. The purge/embargo and deflation harness remains
mission-local until a second mission needs the same adversarial-evaluation
problem. Report stages are where generalization temptation is strongest:
“this worked here” sounds close to “this is platform capability.” The
two-mission gate preserves the distinction. Even a future MET report would not
prove live performance, durable alpha, investment suitability, or that the
assumed impact model matches the market’s response to real orders.
