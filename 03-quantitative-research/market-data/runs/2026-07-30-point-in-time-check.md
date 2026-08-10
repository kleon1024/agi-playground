# Run — stage 00 market data, point-in-time check against live APIs

**Date:** 2026-07-30
**Hardware:** Apple Silicon (arm64, macOS Darwin 24.6.0), CPU-only, no GPU
involved anywhere in this stage.
**Cost:** \$0 (two free public APIs, no key, no paid tier).

## Command — corporate-action adjustment and split check, MSFT

```bash
python core/point_in_time.py --ticker MSFT --range 2y --cik 789019 --tag Assets
```

```
=== corporate-action adjustment: MSFT (2y) ===
bars: 501  dividends: 8  splits: 0
reconstruction vs vendor adjclose — median rel error: 0.000000  max rel error: 0.000000  (n=501)

=== point-in-time fundamentals: CIK 789019, tag Assets ===
facts returned: 142
period 2015-06-30: first filed 2015-07-31 = 176,223,000,000 (10-K); latest filed 2016-07-28 = 174,472,000,000 (10-K)
naive join keyed only on fiscal period 2015-06-30: 174,472,000,000 (silently the latest restatement, filed 2016-07-28)
point-in-time value as of 2015-07-31: 176,223,000,000 (filed 2015-07-31)
```

Sample of the 501 fetched bars (unix timestamp converted to UTC date):

| date | close | adjclose |
|---|---:|---:|
| 2024-07-30 | 422.92 | 416.38 |
| 2024-07-31 | 418.35 | 411.88 |
| 2024-08-01 | 417.11 | 410.66 |
| 2026-07-27 | 389.10 | 389.10 |
| 2026-07-28 | 393.35 | 393.35 |
| 2026-07-29 | 390.54 | 390.54 |

First 3 fetched dividend events:

| ex-date | amount |
|---|---:|
| 2024-08-15 | 0.75 |
| 2024-11-21 | 0.83 |
| 2025-02-20 | 0.83 |

Reconstructed dividend-adjusted close matched Yahoo's own `adjclose` exactly
(median and max relative error both `0.000000` over 501 bars) — no split in
this 2-year window, so the reconstruction only had to absorb 8 dividend
events, and it did so with no measurable residual.

The restatement gap is real and load-bearing: Microsoft's FY2015 (period end
2015-06-30) total assets were first filed on 2015-07-31 at \$176,223,000,000,
then revised to \$174,472,000,000 in a 10-K filed 2016-07-28 — a
\$1,751,000,000 (0.99%) downward restatement thirteen months later.
`naive_lookup` (keyed only on fiscal period) returns the revised figure
unconditionally; `point_in_time_value(as_of=2015-07-31)` correctly returns the
original, because 2016-07-28 had not happened yet on that date.

## Command — split check, NVDA

```bash
python core/point_in_time.py --ticker NVDA --range 5y --cik 1045810 --tag Assets
```

```
=== corporate-action adjustment: NVDA (5y) ===
bars: 1254  dividends: 20  splits: 1
split 1718026200: declared ratio 10.00, day-over-day close ratio 1.0075 -> already applied by vendor
reconstruction vs vendor adjclose — median rel error: 0.000000  max rel error: 0.000000  (n=1254)

=== point-in-time fundamentals: CIK 1045810, tag Assets ===
facts returned: 136
period 2015-01-25: first filed 2015-03-12 = 7,201,368,000 (10-K); latest filed 2016-03-17 = 7,201,000,000 (10-K)
naive join keyed only on fiscal period 2015-01-25: 7,201,000,000 (silently the latest restatement, filed 2016-03-17)
point-in-time value as of 2015-03-12: 7,201,368,000 (filed 2015-03-12)
```

`split` timestamp `1718026200` is `2024-06-10 13:30:00 UTC` — NVDA's real,
publicly documented 10-for-1 split ex-date. The measured day-over-day close
ratio across that date is `1.0075`, close to 1.0 rather than close to
`1/10 = 0.1`: `close` already reflects the split upstream, exactly as
`check_split_already_applied`'s docstring claims, confirmed here against a
real split rather than only asserted. The reconstruction again matches
vendor `adjclose` with zero measurable residual across all 1,254 bars.

NVDA's own `Assets` restatement gap is real but small (a
\$368,000 difference between the first- and second-filed value for period
2015-01-25 — a rounding-level correction, not a substantive one). The MSFT
example above is the more instructive restatement to read first for that
reason; both are genuine API output, not constructed examples.

## Verdict

Both live-API paths ran clean against real tickers with no errors, no
missing fields, and no retries needed. The corporate-action reconstruction
matched the vendor's own adjusted series exactly in both cases. The
point-in-time/naive-lookup divergence is real and quantifiable, not merely
asserted: on MSFT's Assets history it is a 0.99%, thirteen-month-late
correction; a live system relying on `naive_lookup` would have silently used
a number that did not exist yet on the date it claims to be evaluating.

Status of `03-quantitative-research/00-market-data/README.md` was
NOT promoted to `verified` — full mission-stage verification per this
repo's convention expects this to also be exercised against the delisted/
acquired-ticker case from the chapter's own exercises, which this run did
not attempt. Both live paths this run exercised are grounded in this file.
