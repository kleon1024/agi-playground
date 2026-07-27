"""The same two mechanisms as `core/point_in_time.py`, built the way a
production research desk actually would: vectorized ordered joins via
pandas' `merge_asof`, not a hand-rolled backward loop over a Python list.

Requires `pip install pandas requests` — neither is part of this repository's
base dependency group, the same way mission 01's `prod/fineweb_recipe.py`
needs `datatrove` installed separately. That is deliberate: `core/` stays
dependency-light and CPU-portable; `prod/` is allowed to assume a real data
science environment.

Two things a real desk would also do, which this file still does not attempt,
because they cost money rather than complexity:

* swap Yahoo Finance and SEC EDGAR for a licensed point-in-time vendor (a
  survivorship-bias-free CRSP or Compustat point-in-time database, or a
  commercial terminal feed) that guarantees restatement history and universe
  membership out of the box, instead of reconstructing an approximation of it
  from two free APIs;
* backfill a full historical index-membership file across every rebalance
  date, rather than one already-known ticker at a time — recovering
  survivorship-bias-free coverage means starting from what the index *used to
  contain*, not what a single well-known company's history looks like today.

Run:  python point_in_time_pandas.py --ticker AAPL --cik 320193 --tag Assets
"""

from __future__ import annotations

import argparse

import pandas as pd
import requests

_HEADERS = {"User-Agent": "agi-playground research contact@example.com"}


def fetch_price_frame(ticker: str, range_: str = "2y") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Same Yahoo chart endpoint as core/, parsed into two tidy frames."""
    url = (
        f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}"
        f"?range={range_}&interval=1d&events=div,splits"
    )
    payload = requests.get(url, headers=_HEADERS, timeout=20).json()
    result = payload["chart"]["result"][0]
    prices = pd.DataFrame(
        {
            "date": pd.to_datetime(result["timestamp"], unit="s").normalize(),
            "close": result["indicators"]["quote"][0]["close"],
        }
    ).dropna(subset=["close"]).sort_values("date").reset_index(drop=True)

    dividend_events = result.get("events", {}).get("dividends", {})
    dividends = pd.DataFrame(
        [
            {"date": pd.to_datetime(e["date"], unit="s").normalize(), "dividend": e["amount"]}
            for e in dividend_events.values()
        ]
    )
    return prices, dividends


def reconstruct_adjusted_close(prices: pd.DataFrame, dividends: pd.DataFrame) -> pd.Series:
    """Dividend back-adjustment as one reverse-cumulative product.

    `core/point_in_time.py` walks the list backward with an explicit loop so
    the mechanism is visible one day at a time. Production code expresses the
    identical recurrence as a vectorized reverse cumulative product: the
    multiplier for day i is the product of every later day's dividend factor,
    which is a reversed `cumprod` shifted by one row. Same recurrence, same
    result, no explicit loop — and, same as core/, splits are not re-applied
    here, because Yahoo's `close` already reflects them (see
    `../core/point_in_time.py`'s `check_split_already_applied`).
    """
    merged = prices.merge(dividends, on="date", how="left")
    prior_close = merged["close"].shift(1)
    per_day_factor = (1 - merged["dividend"].fillna(0) / prior_close.replace(0, pd.NA)).fillna(1.0)
    factor_after_today = per_day_factor[::-1].cumprod()[::-1].shift(-1).fillna(1.0)
    return (merged["close"] * factor_after_today).rename("reconstructed_adjclose")


def fetch_fundamentals_frame(cik: int, tag: str, taxonomy: str = "us-gaap") -> pd.DataFrame:
    """Same SEC EDGAR endpoint as core/, flattened into one tidy frame."""
    url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik:010d}/{taxonomy}/{tag}.json"
    payload = requests.get(url, headers=_HEADERS, timeout=20).json()
    rows = [
        {"fiscal_end": f["end"], "filed": f["filed"], "value": f["val"], "form": f.get("form", "")}
        for unit_facts in payload.get("units", {}).values()
        for f in unit_facts
        if "end" in f and "filed" in f
    ]
    frame = pd.DataFrame(rows)
    frame["fiscal_end"] = pd.to_datetime(frame["fiscal_end"])
    frame["filed"] = pd.to_datetime(frame["filed"])
    return frame.sort_values("filed").reset_index(drop=True)


def point_in_time_join(prices: pd.DataFrame, fundamentals: pd.DataFrame) -> pd.DataFrame:
    """The production version of `core/point_in_time.py`'s `point_in_time_value`:
    one ordered merge instead of a per-date scan.

    `pandas.merge_asof(..., direction="backward")` is exactly the point-in-time
    discipline this stage is about, expressed in one call: for every price
    date, attach the most recent fundamentals row whose `filed` date is at or
    before that price date, and nothing filed later. That single keyword is
    the entire guardrail — changing it to `"nearest"`, or dropping it and
    relying on a default that differs across pandas versions, silently
    reintroduces the look-ahead bug `core/` exists to make visible.
    """
    return pd.merge_asof(
        prices.sort_values("date"),
        fundamentals.sort_values("filed"),
        left_on="date",
        right_on="filed",
        direction="backward",
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", default="AAPL")
    ap.add_argument("--range", default="2y")
    ap.add_argument("--cik", type=int, default=320193, help="SEC CIK, default Apple Inc.")
    ap.add_argument("--tag", default="Assets", help="us-gaap XBRL concept")
    args = ap.parse_args()

    prices, dividends = fetch_price_frame(args.ticker, args.range)
    prices["reconstructed_adjclose"] = reconstruct_adjusted_close(prices, dividends)

    fundamentals = fetch_fundamentals_frame(args.cik, args.tag)
    joined = point_in_time_join(prices[["date", "close", "reconstructed_adjclose"]], fundamentals)
    print(joined[["date", "close", "reconstructed_adjclose", "fiscal_end", "filed", "value", "form"]].tail())


if __name__ == "__main__":
    main()
