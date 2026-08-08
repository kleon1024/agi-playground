---
status: verified
level: foundation
verified: 2026-07-30
---

# What did you actually know on the decision date?

**Goal:** turn two free, public market data feeds into a panel that answers
one question honestly for every row: *what was actually knowable on this
date?* Get that wrong and nothing built on top of this stage — a signal, a
backtest, a Sharpe ratio — means anything, no matter how careful the modeling
is downstream.

**Before this:** [why this mission is the hardest test of the architecture](../README.md),
for why a domain where the data actively fights back needs strictly more
evaluation discipline than mission 01's text or mission 02's logged clicks.

**Why this is stage 00 and not a data-loading afterthought.** Start from a
tidy CSV of "historical prices," the way most backtest tutorials do, and the
decisions that decide whether the result is honest are already made and
hidden from you. Is that CSV missing every company that went bankrupt or got
acquired during the window? Are prices adjusted the same way a live system
would have seen them at the time? Does a fundamentals column for "Q2 2015"
reflect the number readable on any day *during* 2015, or the number as later
revised? Each is a way a backtest can quietly already know the future, and
each inflates a result the same direction: better than reality. Mirroring
[mission 01's stage 00](../../01-language-model/00-corpus/), this
lesson comes before anything else, because it is what the rest of the
mission has to be correct with respect to.

## The bias catalogue

These four biases, and the discipline of naming an availability timestamp
for every fact, are not this stage's own discovery — survivorship bias in
backtests is documented at least as far back as Elton, Gruber & Blake,
*"Survivorship Bias and Mutual Fund Performance"* (Review of Financial
Studies, 1996), and the point-in-time database as a commercial category
(Compustat's, most notably) exists specifically because this class of error
was common enough in academic and practitioner backtests to be worth paying
to eliminate.

**Survivorship bias.** Build a universe from today's index constituents and
project it backward, and you silently drop every name that was delisted,
merged away, or went bankrupt during the study period. Because the failures
are exactly the names that disappear, this is not neutral noise — it moves
every downstream result in the same direction, making the past look better
than it was.

**Corporate-action adjustment.** A raw closing price is not comparable to
itself across a stock split or a dividend payment — the same company's share
count and per-share economics change on the ex-date. Getting this wrong turns
out to be easy: this stage's `core/` implementation first tried to re-apply a
declared 10-for-1 split to a "raw" closing-price series from Yahoo Finance's
chart endpoint, and every price came out wrong by almost exactly the split
ratio, uniformly — not scattered error, a systematic multiplier. The cause:
that endpoint's plain `close` field is already restated for historical
splits, so re-adjusting it double-counted the correction. `core/point_in_time.py`
now checks this explicitly instead of assuming it — `check_split_already_applied`
compares the day-over-day price ratio across a split's ex-date to the
declared ratio, telling a real discontinuity and an already-adjusted series
apart before reconstructing anything on top of them. Trusting a vendor
field's name over what it actually contains is exactly the error this stage
exists to catch, including when it happens to the person building the lesson.

**Look-ahead through restated fundamentals.** Ask when a number reported "for"
a fiscal quarter actually became public, and the answer is never the last day
of that quarter — it becomes public on the date it is filed, routinely one to
three months later, and it can be revised afterward: a first 10-Q figure
superseded by a later 10-K, an amendment, a restatement. Query SEC EDGAR's
XBRL API for one concept and you get exactly this structure back: every
historical value carries both the fiscal period it describes and the date it
was actually filed, and the same period frequently has more than one filed
value. "The" value for a quarter is therefore not a single number independent
of when you ask — it depends on the as-of date, and joining on fiscal period
alone silently hands you the most-recently-revised number on a date when only
the original, unrevised one existed.

**Timestamp discipline.** Look back at all three biases above and you find one
discipline wearing different clothes: every fact needs an availability
timestamp, not just a value, and every join across data sources has to respect
it. A price is knowable the moment the market prints it; a fundamental is
knowable only once filed; a universe membership is knowable only for names
that existed on that date. Making that timestamp explicit everywhere it was
implicit is this stage's entire job.

## What you build

Two free, genuinely public sources, no API key for either:

* **Yahoo Finance's chart endpoint** — daily OHLC, a vendor-computed adjusted
  close, and the raw dividend/split event list an adjustment is built from.
* **SEC EDGAR's XBRL company-concept API** — every historical value a company
  has ever reported for one accounting concept, each carrying both its fiscal
  period end and its public filing date.

`core/point_in_time.py` — stdlib only (`urllib`, `json`, `statistics`,
`dataclasses`), talking to both endpoints directly:

| Function | What it does | Why it exists |
|---|---|---|
| `fetch_price_history` | Pull bars, dividends, and splits for one ticker | Raw material every adjustment and bias check needs |
| `check_split_already_applied` | Compare day-over-day price ratio to a declared split ratio | Catches double-adjustment, from a real bug found writing this stage |
| `reconstruct_adjusted_close` | Rebuild the dividend-only backward adjustment by hand | Makes "adjusted close" arithmetic legible instead of trusting a vendor column |
| `fetch_edgar_concept` | Pull every filed value for one XBRL concept, with fiscal end and filed date | Raw material a point-in-time fundamentals join needs |
| `naive_lookup` vs `point_in_time_value` | The wrong join (keyed on period alone) beside the right one (filed at-or-before an as-of date) | Puts the look-ahead bug and its fix side by side |
| `find_restatement_gap` | Locate a real period with more than one filed value | Turns "fundamentals get restated" into a concrete example |

## What the raw output actually looks like

Run the MSFT command below and read what actually comes back, instead of
taking the mechanism's claims on faith:

```
$ python core/point_in_time.py --ticker MSFT --range 2y --cik 789019 --tag Assets
=== corporate-action adjustment: MSFT (2y) ===
bars: 501  dividends: 8  splits: 0
reconstruction vs vendor adjclose — median rel error: 0.000000  max rel error: 0.000000  (n=501)

=== point-in-time fundamentals: CIK 789019, tag Assets ===
facts returned: 142
period 2015-06-30: first filed 2015-07-31 = 176,223,000,000 (10-K); latest filed 2016-07-28 = 174,472,000,000 (10-K)
naive join keyed only on fiscal period 2015-06-30: 174,472,000,000 (silently the latest restatement, filed 2016-07-28)
point-in-time value as of 2015-07-31: 176,223,000,000 (filed 2015-07-31)
```

That restatement is real: Microsoft's FY2015 total assets were first filed at
\$176.223B, then revised down by \$1.75B — about 1% — thirteen months later. A
naive join keyed only on fiscal period 2015-06-30 hands you the revised
\$174.472B figure even when you ask "what did the market know on 2015-07-31,"
the day the original 10-K posted. `point_in_time_value` returns the right
number, \$176.223B, because it respects the filed date instead of the fiscal
period alone.

Three of MSFT's 501 fetched bars, so you can see the shape of what
`fetch_price_history` returns:

| date | close | adjclose |
|---|---:|---:|
| 2024-07-30 | 422.92 | 416.38 |
| 2024-08-01 | 417.11 | 410.66 |
| 2026-07-29 | 390.54 | 390.54 |

The split check runs the same way against a real split. NVDA's declared
10-for-1 split lands on 2024-06-10:

```
$ python core/point_in_time.py --ticker NVDA --range 5y --cik 1045810 --tag Assets
split 1718026200: declared ratio 10.00, day-over-day close ratio 1.0075 -> already applied by vendor
```

A day-over-day ratio of 1.0075 — not 0.1 — is the tell: if Yahoo's `close`
were genuinely raw, that ratio would collapse to roughly a tenth across the
split's ex-date. It doesn't, so `close` already reflects the split, and
`reconstruct_adjusted_close` correctly leaves it alone instead of dividing
every pre-split price by ten a second time.

<!-- interactive: PointInTimeJoin -->

## Reproducing

```bash
python core/point_in_time.py --ticker MSFT --range 2y --cik 789019 --tag Assets
python core/point_in_time.py --ticker NVDA --range 5y --cik 1045810 --tag Assets
```

Any ticker and CIK work; MSFT is a clean dividend-only example, and NVDA's
2024 ten-for-one split is a real, publicly verifiable exercise of the split
check above. Runs in seconds on one CPU core with no GPU involved anywhere in
this stage.

## The production lane

`prod/point_in_time_pandas.py` performs the identical two reconstructions with
`pandas` — a different *shape*, not just more code. `core/`'s dividend
adjustment loops backward over a list one bar at a time, because a loop keeps
the recurrence readable; `prod/`'s is a reversed cumulative product over a
`pandas.Series`, the same recurrence vectorized. `core/`'s point-in-time join
is a function called once per as-of-date; `prod/`'s is one
`pandas.merge_asof(..., direction="backward")` call across the whole panel —
the idiomatic way to express an ordered, point-in-time-correct join, and the
keyword argument carrying this stage's entire discipline. Change
`"backward"` to `"nearest"`, or drop it and inherit a library default, and
the look-ahead bug is back, silently, inside one line instead of an obvious
loop.

Neither lane guarantees a *survivorship-bias-free universe* with free data:
Yahoo and EDGAR answer questions about a company you already know to ask
about, not the historical membership list of an index including every name
that stopped existing. That is what a licensed point-in-time vendor —
CRSP, Compustat, a commercial data terminal — is actually paying for, and no
amount of cleverness against a free API substitutes for it. Naming that
limit here, rather than pretending two free endpoints solved it, is itself
part of the discipline.

## The fix and its trade

The failure is that every join in a backtest quietly answers *which*
restatement the market could see, and the naive answer is wrong in one
direction. Measured across all 69 AAPL fiscal periods, a join keyed only on
fiscal period mismatched the filed-at-the-time value on 4% of periods, with
mean error 1.65% and a worst case of 3.83% of equity; Microsoft's FY2015
assets were first filed at \$176.223B on 2015-07-31 and restated down by
\$1.75B — about 1% — thirteen months later, so "what did the market know on
2015-07-31" has two defensible answers and the naive join silently picks the
wrong one. The same trust-the-field-name error hits prices: NVDA's declared
10-for-1 split shows a day-over-day close ratio of 1.0075, not 0.1, so the
vendor already applied the split and re-applying it would divide every
pre-split price by ten a second time.

The fix is availability-timestamp discipline enforced at the join: every
fact carries a filed date alongside its value, the join is an as-of join
(`pandas.merge_asof(..., direction="backward")` in the production lane)
that returns the value filed at or before the decision date rather than the
newest database value, and the split check compares a measured day-over-day
ratio to a declared ratio before reconstructing anything. The trade is
freshness for correctness: an as-of panel deliberately lags the newest
restatement, because a value that was not knowable on the decision date is
not a value the market could have traded on. Survivorship is the boundary
the trade cannot buy with free data — only a licensed point-in-time vendor
(CRSP, Compustat) supplies the historical universe including every name
that stopped existing, and the discipline's cost is that the panel's answer
is only ever as honest as the timestamps each source provides.

## Who owns the loop

- **The data owner** owns the availability timestamp: every price, filing,
  and universe membership carries when it was knowable, and the
  survivorship-free universe is a licensed point-in-time vendor's product,
  not a free endpoint's. Elton, Gruber & Blake (Review of Financial
  Studies, 1996) document survivorship bias in backtests at least that far
  back, and the point-in-time database as a commercial category exists
  because this class of error was common enough to be worth paying to
  eliminate.
- **The research platform** owns the join: filed-date joins with
  `direction="backward"`, the split sanity check, and the guarantee that no
  downstream table can silently substitute a later restatement for the
  value knowable on a given date.
- **The strategy team** owns what it inherits: every signal and backtest on
  this panel inherits both the fix and the residual boundaries — free-data
  survivorship limits and restatement frequency that varies by concept,
  which a first-pass filter on a few XBRL tags makes visible.

When the ownership is implicit, the data team ships "adjusted" prices
without saying what they adjusted for, the platform joins on fiscal period,
and the strategy inherits a look-ahead it never sees — the symptom this
stage opened with.

## Exercises

1. **Break the split check.** Point `check_split_already_applied` at an old
   split versus a recent one and compare the ratios — vendors change
   conventions, so do not assume today's behavior held historically.
2. **Find your own restatement.** Run `find_restatement_gap` across a few
   XBRL tags for the same company. Some concepts restate far more than
   others — a first-pass filter for how much discipline a signal needs.
3. **Quantify the look-ahead gap.** For a restated period, measure the days
   between the fiscal period's end and its first filing — that is how much
   of a naive backtest's foresight is just early earnings.
4. **Try a delisted or acquired ticker.** Confirm whether these endpoints
   return history for a company that no longer trades, and if not, note how
   that absence biases a naive backtest.

## Next

Stage 01 (planned): candidate signal construction, drawing only on values this
stage's point-in-time discipline certifies as knowable on each decision date —
with a disclosed log of every variant tried, since that log is what stage 03
needs to compute a deflated Sharpe ratio honestly.

A detour from here: [the as-of join, and the restatement it
catches](asof-vs-naive/) — the naive join measured across all 69 fiscal
periods: 4% silently wrong, mean error 1.65%, worst case 3.83% of equity —
always in the look-ahead direction.

Another detour: [the same period, two values, filed a year apart](the-restatement-gap/) — the recorded point-in-time check read: FY2015 carries two values (176.2B filed 2015, 174.5B restated 2016), and the naive join silently uses the restatement.
