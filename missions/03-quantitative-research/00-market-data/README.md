---
status: draft
level: foundation
---

# What did you actually know on the decision date?

**Goal:** turn two free, public market data feeds into a panel that answers
one question honestly for every row: *what was actually knowable on this
date?* Get that wrong and nothing built on top of this stage — a signal, a
backtest, a Sharpe ratio — means anything, no matter how careful the modeling
is downstream.

**Why this is stage 00 and not a data-loading afterthought.** Every backtest
tutorial that starts from a tidy CSV of "historical prices" has already made
the decisions that decide whether the result is honest, and hidden them from
the reader. Is that CSV missing every company that went bankrupt or got
acquired during the window? Are the prices adjusted for splits and dividends,
and adjusted the same way a live system would have seen them at the time? Does
a fundamentals column for "Q2 2015" actually reflect the number a researcher
could have read on any day *during* 2015, or the number as later revised? Each
of these is a way a backtest can quietly already know the future, and each one
inflates a result in the same direction: better than reality. Mirroring
[mission 01's stage 00](../../01-language-model-agent/00-corpus/), we build the
lesson before anything else, because the lesson is what the rest of the
mission has to be correct with respect to.

## The bias catalogue

**Survivorship bias.** A universe built from today's index constituents and
projected backward silently drops every name that was delisted, merged away,
or went bankrupt during the study period. Because failures are the names that
disappear, this bias is not neutral noise — it moves every downstream result
in exactly one direction, making the past look better than it was.

**Corporate-action adjustment.** A raw closing price is not comparable to
itself across a stock split or a dividend payment; the same company's share
count and per-share economics change on the ex-date. Getting the adjustment
wrong, or getting it wrong in a specific, informative way, turns out to be
easy: this stage's own `core/` implementation first tried to re-apply a
declared 10-for-1 stock split to a "raw" closing-price series pulled from
Yahoo Finance's chart endpoint, and every single price in the reconstruction
came out wrong by almost exactly the split ratio, uniformly, on every date —
not scattered error, a systematic multiplier. The reason was worth finding:
that endpoint's plain `close` field is already restated for historical
splits, so treating it as raw and re-adjusting double-counted the correction.
`core/point_in_time.py` now checks this explicitly instead of assuming it —
`check_split_already_applied` compares the day-over-day price ratio across a
split's ex-date to the declared ratio, so a real discontinuity and an
already-adjusted series are told apart before anything is reconstructed on
top of them. Trusting a vendor field's name over what it actually contains is
exactly the kind of error this stage exists to catch, including when it
happens to the person building the lesson about it.

**Look-ahead through restated fundamentals.** A number reported "for" a fiscal
quarter is not public knowledge on the last day of that quarter; it becomes
public on the date it is filed, which is routinely one to three months later,
and it can be revised afterward — a first 10-Q figure superseded by a later
10-K, an amendment, a restatement. SEC EDGAR's XBRL API returns exactly this
structure: every historical value carries both the fiscal period it describes
and the date it was actually filed, and the same period frequently has more
than one filed value. "The" value for a quarter is therefore not a single
number independent of when you ask — it depends on the as-of date, and a join
keyed only on fiscal period silently hands a backtest the most-recently-
revised number on a date when only the original, unrevised one existed.

**Timestamp discipline.** All three biases above are really one discipline
wearing different clothes: every fact needs an availability timestamp, not
just a value, and every join across data sources has to respect it. A price is
knowable the moment the market prints it; a fundamental is knowable only once
filed; a universe membership is knowable only for names that existed on that
date. Stage 00's entire job is making that timestamp explicit everywhere it
was implicit.

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
| `fetch_price_history` | Pull bars, dividends, and splits for one ticker | The raw material every adjustment and every bias check needs |
| `check_split_already_applied` | Compare day-over-day price ratio to a declared split ratio | Catches double-adjustment before it happens, from a real bug found writing this stage |
| `reconstruct_adjusted_close` | Rebuild the dividend-only backward adjustment by hand | Makes the arithmetic behind "adjusted close" legible instead of trusting a vendor column |
| `fetch_edgar_concept` | Pull every filed value for one XBRL concept, with fiscal end and filed date | The raw material a point-in-time fundamentals join needs |
| `naive_lookup` vs `point_in_time_value` | The wrong join (keyed on period alone) beside the right one (filed at-or-before an as-of date) | Puts the look-ahead bug and its fix side by side in the same function signature |
| `find_restatement_gap` | Locate a real period with more than one filed value | Turns "fundamentals get restated" from an abstract warning into a concrete, inspectable example |

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
`pandas`, and the difference is not "more code, more libraries" — it is a
different *shape* of solution. `core/`'s dividend adjustment is a backward
Python loop over a list, one bar at a time, because a loop is what makes the
recurrence readable. `prod/`'s version is a reversed cumulative product over a
`pandas.Series` — the same recurrence, vectorized. More importantly,
`core/`'s point-in-time fundamentals join is a function called once per
as-of-date; `prod/`'s is a single `pandas.merge_asof(..., direction="backward")`
call across the whole panel at once — the idiomatic, production way to express
an ordered, point-in-time-correct join, and the keyword argument that carries
the entire discipline this stage is about. Change `"backward"` to `"nearest"`,
or drop it and inherit whatever a library version defaults to, and the
look-ahead bug this stage exists to catch is back, silently, inside one line
instead of an obvious loop.

What `prod/` still cannot do with free data: guarantee a *survivorship-bias-free
universe*. Yahoo and EDGAR answer questions about a company you already know
to ask about; neither hands you the historical membership list of an index
including every name that stopped existing. That is what a licensed
point-in-time vendor — CRSP, Compustat, or a commercial data terminal — is
actually paying for, and no amount of cleverness against a free API fully
substitutes for it. Naming that limit here, rather than pretending two free
endpoints solved it, is itself part of the discipline.

## Exercises

1. **Break the split check.** Point `check_split_already_applied` at a ticker
   whose split happened many years ago and compare the day-over-day ratio to
   one from a recent split. Vendors change conventions; do not assume today's
   behavior held historically.
2. **Find your own restatement.** Run `find_restatement_gap` against a few
   different XBRL tags (`Assets`, `Revenues`, `NetIncomeLoss`) for the same
   company. Some concepts restate far more than others — a first-pass filter
   for how much point-in-time discipline a given signal actually needs.
3. **Quantify the look-ahead gap.** For a restated period, compute how many
   days elapsed between the fiscal period's end and its first legitimate
   filing date. That gap is exactly how much of a naive backtest's apparent
   foresight is actually just knowing next quarter's earnings early.
4. **Try a delisted or acquired ticker.** Confirm whether these free endpoints
   even return history for a company that no longer trades, and if not, note
   precisely how that absence would bias a naive backtest — this is
   survivorship bias made concrete rather than asserted.

## Next

Stage 01 (planned): candidate signal construction, drawing only on values this
stage's point-in-time discipline certifies as knowable on each decision date —
with a disclosed log of every variant tried, because that log is what stage 03
needs to compute a deflated Sharpe ratio honestly.
