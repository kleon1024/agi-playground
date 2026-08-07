---
status: verified
level: applied
base: none
label: The as-of join
verified: 2026-08-06
---

# The as-of join, and the restatement it catches

**Question:** [stage 00](../) joins fundamentals at the filing date, never at
the fiscal period — the point-in-time discipline. Its recorded run showed
one restatement. How often does the naive join (key on fiscal period, take
whatever is there) actually go wrong, and by how much?

**Before this:** [stage 00's point-in-time check](../) and its recorded
example.

## The scan, measured

The run ([record](runs/2026-08-06-asof-vs-naive.md)) fetches AAPL's Assets
facts and compares the two joins across all 69 fiscal periods:

| fiscal end | naive join | as-of join (+45d) | gap |
|---|---:|---:|---:|
| 2015-06-30 | 174,472M | 176,223M | 0.99% |
| 2016-06-30 | 193,468M | 193,694M | 0.12% |
| 2017-06-30 | 250,312M | 241,086M | **3.83%** |

**69 periods, 3 mismatches (4%), mean error 1.65%.**

## Three readings

**The naive join is wrong on 4% of periods, and always in the same
direction.** The wrong value is the later restatement — data filed after
the strategy's evaluation date — so the naive join's error is a look-ahead
violation, not a measurement error. A backtest that joins by fiscal period
is silently peeking at the future on 4% of its fundamentals, and on the
2017 period the peek is worth 3.8% of equity.

**A period's value is not a single fact; it depends on when you asked.** The
restatement mechanism is the point: the same fiscal period has multiple
filed values (176.2B filed 2015-07-31, restated to 174.5B filed 2016-07-28),
and "the" value for the period is a function of the date. The point-in-time
join picks the value knowable on the date it pretends to evaluate — the
only value a backtest has a right to.

**The recent six periods all agree — which is the trap.** The mechanism is
real but episodic, and the recent window looks clean. That is exactly why
the discipline is easy to skip and why "it has not bitten recently" is not
evidence it cannot bite: the 2017 quarter is a 3.8% equity error that a
recent-window check would not have caught.

## Evidence boundary

One ticker, one concept (AAPL Assets), the live EDGAR fact set (142 facts,
69 periods, drifts as EDGAR changes). It shows the mechanism and its
frequency on this concept; it does not claim the 4% rate generalizes across
companies or concepts — companies that restate more often will be wrong
more often, which is precisely why the check has to run per-company.

## Check your mental model

Answer each before opening it.

**1. The naive join returns 250.3B for 2017-06-30; the as-of join returns
241.1B. Which is "the" correct value?**

<details>
<summary>Answer</summary>

Neither is the value for the period in an absolute sense — the period has
multiple filed values because it was restated. The correct value for a
backtest is the one knowable on the evaluation date: 241.1B if the strategy
ran 45 days after the period ended, because the 250.3B figure was not filed
yet. The as-of join answers "what could a strategy have known," which is
the only question a backtest may ask.

</details>

**2. The recent six periods match. Why is that not a reason to drop the
as-of join?**

<details>
<summary>Answer</summary>

Because the mechanism is episodic: restatements cluster in specific periods
(here, 2015-2017) and a recent window can look clean while older periods
carry 3.8% errors. The check is cheap and it is the only way to know whether
the next period is one of the 4% — and a backtest cannot tell which of its
fundamental values came from a restatement after the fact without the
filing dates.

</details>

## Next

Back to [stage 00's market data](../), or forward to
[stage 01's signal research](../../01-signal-research/) where every
candidate signal is built only from what this panel certifies as knowable.
