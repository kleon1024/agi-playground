"""From-scratch point-in-time market data: two public sources, two biases.

Every function here talks to a real, free, public endpoint directly through
the standard library — no data vendor SDK, no pandas. The point of writing it
this way is that both biases this stage exists to catch are visible in the
raw JSON before any convenience layer smooths them out:

1. **Corporate-action adjustment.** A raw closing price is not comparable
   across a stock split or a dividend. `reconstruct_adjusted_close` rebuilds
   the dividend adjustment from the raw event list and checks it against the
   vendor's own adjusted series — so the adjustment is verified, not assumed.
   `check_split_already_applied` exists because of a real bug this file's
   first draft had: this vendor's plain `close` field is already restated for
   historical stock splits, so re-applying the split ratio from its own event
   list silently double-adjusts the series by exactly that ratio. Assuming a
   vendor's fields mean what a textbook says they mean, instead of checking,
   is precisely the failure mode this stage exists to catch — including when
   it happens to the person writing the lesson about it.
2. **Look-ahead through restated fundamentals.** A number "for" a fiscal
   quarter is not public until it is filed, and it can be revised afterward.
   `point_in_time_value` answers "what was knowable on date X", which is a
   different question from "what is the value for that period today", and
   confusing the two is exactly how a backtest quietly sees the future.

Data sources (both free, no API key):

* Yahoo Finance's chart endpoint — daily OHLC, adjusted close, and the raw
  split/dividend event list a real adjustment is built from.
* SEC EDGAR's XBRL company-concept API — every historical value a company has
  ever reported for one accounting concept, each carrying both its fiscal
  period end and the date it was actually filed with the SEC.

Run:  python point_in_time.py --ticker AAPL --cik 320193 --tag Assets
"""

from __future__ import annotations

import argparse
import json
import statistics
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date

# SEC's Fair Access policy requires a descriptive User-Agent identifying the
# requester; requests without one are throttled or refused. This is a real
# operational detail, not decoration — the first thing everyone's EDGAR script
# breaks on is skipping this header.
_HEADERS = {"User-Agent": "agi-playground research contact@example.com"}


def _fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


# --------------------------------------------------------------------------
# 1. Corporate-action adjustment
# --------------------------------------------------------------------------


@dataclass
class DailyBar:
    ts: int  # unix seconds, exchange-local trading day
    close: float
    adjclose: float | None


def fetch_price_history(ticker: str, range_: str = "2y") -> tuple[list[DailyBar], list[dict], list[dict]]:
    """Return (bars, dividend events, split events) from Yahoo's chart API.

    Splits and dividends come back as separate event dictionaries keyed by the
    same unix timestamps as the bars, which is exactly the join a from-scratch
    adjustment has to perform by hand.
    """
    url = (
        f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}"
        f"?range={range_}&interval=1d&events=div,splits"
    )
    payload = _fetch_json(url)
    result = payload["chart"]["result"][0]
    timestamps = result["timestamp"]
    closes = result["indicators"]["quote"][0]["close"]
    adjcloses = result["indicators"].get("adjclose", [{}])[0].get("adjclose")
    bars = [
        DailyBar(ts=ts, close=c, adjclose=(adjcloses[i] if adjcloses else None))
        for i, (ts, c) in enumerate(zip(timestamps, closes))
        if c is not None
    ]
    events = result.get("events", {})
    dividends = sorted(events.get("dividends", {}).values(), key=lambda e: e["date"])
    splits = sorted(events.get("splits", {}).values(), key=lambda e: e["date"])
    return bars, dividends, splits


def check_split_already_applied(bars: list[DailyBar], splits: list[dict]) -> list[dict]:
    """Sanity-check whether `close` already reflects a declared split.

    If `close` is genuinely raw (not split-adjusted), the day-over-day ratio
    across a split's ex-date should be close to the split ratio itself — an
    N-for-1 split makes the next close roughly 1/N of the previous one. If
    `close` is already split-adjusted upstream, that ratio will instead sit
    near 1.0, because there was never a real discontinuity to begin with.
    This is exactly how the double-adjustment bug in an earlier draft of
    `reconstruct_adjusted_close` was caught: it assumed the first case without
    checking, for a vendor that actually does the second.
    """
    ts_to_idx = {b.ts: i for i, b in enumerate(bars)}
    checks = []
    for e in splits:
        idx = ts_to_idx.get(e["date"])
        if idx is None or idx == 0 or not bars[idx - 1].close:
            continue
        day_over_day = bars[idx].close / bars[idx - 1].close
        checks.append(
            {
                "date": e["date"],
                "declared_ratio": e["numerator"] / e["denominator"],
                "day_over_day_close_ratio": day_over_day,
                "close_already_adjusted": abs(day_over_day - 1.0) < 0.2,
            }
        )
    return checks


def reconstruct_adjusted_close(bars: list[DailyBar], dividends: list[dict]) -> list[float]:
    """Rebuild dividend-adjusted close from `close` plus the dividend events.

    Splits are deliberately not re-applied here: see `check_split_already_applied`
    and the module docstring for why. Dividends are a separate adjustment this
    vendor's `close` does not already include. Walk from the most recent bar to
    the oldest, accumulating a multiplier that applies to every bar strictly
    before an ex-dividend date, never to the ex-date itself (that day's close
    already reflects the payout). A cash dividend d paid against a prior close
    p multiplies every earlier price by (1 - d/p), the fraction of value the
    dividend removed from the stock; the walk goes backward and multiplies
    because the adjustment compounds across multiple dividends.
    """
    n = len(bars)
    ts_to_idx = {b.ts: i for i, b in enumerate(bars)}

    factor_before: dict[int, float] = {}
    for e in dividends:
        idx = ts_to_idx.get(e["date"])
        if idx is None or idx == 0:
            continue
        prior_close = bars[idx - 1].close
        if prior_close:
            factor_before[idx] = factor_before.get(idx, 1.0) * max(1e-9, 1 - e["amount"] / prior_close)

    reconstructed = [0.0] * n
    running = 1.0
    for i in range(n - 1, -1, -1):
        reconstructed[i] = round(bars[i].close * running, 6)
        if i in factor_before:
            running *= factor_before[i]
    return reconstructed


def compare_to_vendor_adjustment(bars: list[DailyBar], reconstructed: list[float]) -> dict:
    """Median and max absolute relative error against the vendor's own adjclose.

    A small residual error is expected (Yahoo also folds in special
    dividends and rounding conventions this reconstruction does not model);
    a *large* one means a split or dividend event was missed, which is the
    failure mode this check exists to catch before the series is used for
    anything downstream.
    """
    errors = [
        abs(reconstructed[i] - b.adjclose) / b.adjclose
        for i, b in enumerate(bars)
        if b.adjclose and b.adjclose > 0
    ]
    if not errors:
        return {"median_rel_error": None, "max_rel_error": None, "n": 0}
    return {
        "median_rel_error": statistics.median(errors),
        "max_rel_error": max(errors),
        "n": len(errors),
    }


# --------------------------------------------------------------------------
# 2. Point-in-time fundamentals
# --------------------------------------------------------------------------


@dataclass
class Fact:
    fiscal_end: date
    filed: date
    value: float
    form: str
    accession: str


def fetch_edgar_concept(cik: int, tag: str, taxonomy: str = "us-gaap") -> list[Fact]:
    """Every historical value SEC EDGAR has for one XBRL concept.

    Each entry carries the fiscal period it describes (`end`) and the date it
    was actually made public (`filed`) — the same fact can appear more than
    once, filed on different dates, when a company amends or restates it.
    """
    url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik:010d}/{taxonomy}/{tag}.json"
    payload = _fetch_json(url)
    facts = []
    for unit_facts in payload.get("units", {}).values():
        for f in unit_facts:
            if "end" not in f or "filed" not in f:
                continue
            facts.append(
                Fact(
                    fiscal_end=date.fromisoformat(f["end"]),
                    filed=date.fromisoformat(f["filed"]),
                    value=float(f["val"]),
                    form=f.get("form", ""),
                    accession=f.get("accn", ""),
                )
            )
    return sorted(facts, key=lambda fa: (fa.fiscal_end, fa.filed))


def naive_lookup(facts: list[Fact], fiscal_end: date) -> Fact | None:
    """What a careless join does: grab whatever value is keyed to this period.

    This silently returns the *latest* filed value for the period — including
    any later restatement — regardless of whether that value existed yet on
    the date the naive code is pretending to evaluate a strategy on.
    """
    candidates = [f for f in facts if f.fiscal_end == fiscal_end]
    return max(candidates, key=lambda f: f.filed) if candidates else None


def point_in_time_value(facts: list[Fact], fiscal_end: date, as_of: date) -> Fact | None:
    """What was actually knowable on `as_of`: the latest filing for this
    period whose filing date has already passed, or None if the period had
    not been reported at all yet.
    """
    candidates = [f for f in facts if f.fiscal_end == fiscal_end and f.filed <= as_of]
    return max(candidates, key=lambda f: f.filed) if candidates else None


def find_restatement_gap(facts: list[Fact]) -> tuple[date, Fact, Fact] | None:
    """Find one fiscal period with two differing filed values, if any exist.

    Returns (fiscal_end, first_filed, latest_filed) for the first period where
    a restatement changed the reported number — direct evidence that "the"
    value for a period is not a single fact independent of when you asked.
    """
    by_period: dict[date, list[Fact]] = {}
    for f in facts:
        by_period.setdefault(f.fiscal_end, []).append(f)
    for end, group in sorted(by_period.items()):
        if len(group) < 2:
            continue
        ordered = sorted(group, key=lambda f: f.filed)
        first, latest = ordered[0], ordered[-1]
        if first.value != latest.value:
            return end, first, latest
    return None


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", default="AAPL")
    ap.add_argument("--range", default="2y")
    ap.add_argument("--cik", type=int, default=320193, help="SEC CIK, default Apple Inc.")
    ap.add_argument("--tag", default="Assets", help="us-gaap XBRL concept")
    args = ap.parse_args()

    print(f"=== corporate-action adjustment: {args.ticker} ({args.range}) ===")
    try:
        bars, dividends, splits = fetch_price_history(args.ticker, args.range)
        print(f"bars: {len(bars)}  dividends: {len(dividends)}  splits: {len(splits)}")
        for check in check_split_already_applied(bars, splits):
            state = "already applied by vendor" if check["close_already_adjusted"] else "NOT applied — reconstruction must handle it"
            print(
                f"split {check['date']}: declared ratio {check['declared_ratio']:.2f}, "
                f"day-over-day close ratio {check['day_over_day_close_ratio']:.4f} -> {state}"
            )
        reconstructed = reconstruct_adjusted_close(bars, dividends)
        stats = compare_to_vendor_adjustment(bars, reconstructed)
        if stats["n"]:
            print(
                f"reconstruction vs vendor adjclose — "
                f"median rel error: {stats['median_rel_error']:.6f}  "
                f"max rel error: {stats['max_rel_error']:.6f}  (n={stats['n']})"
            )
        else:
            print("vendor adjclose unavailable for this range; reconstruction still computed")
    except (urllib.error.URLError, KeyError, IndexError) as exc:
        print(f"price fetch failed ({exc}); skipping this demonstration")

    print()
    print(f"=== point-in-time fundamentals: CIK {args.cik}, tag {args.tag} ===")
    try:
        facts = fetch_edgar_concept(args.cik, args.tag)
        print(f"facts returned: {len(facts)}")
        gap = find_restatement_gap(facts)
        if gap:
            end, first, latest = gap
            print(f"period {end}: first filed {first.filed} = {first.value:,.0f} "
                  f"({first.form}); latest filed {latest.filed} = {latest.value:,.0f} "
                  f"({latest.form})")
            as_of = first.filed
            naive = naive_lookup(facts, end)
            pit = point_in_time_value(facts, end, as_of)
            print(f"naive join keyed only on fiscal period {end}: {naive.value:,.0f} "
                  f"(silently the latest restatement, filed {naive.filed})")
            print(f"point-in-time value as of {as_of}: "
                  f"{pit.value:,.0f} (filed {pit.filed})" if pit else
                  f"point-in-time value as of {as_of}: not yet filed")
        else:
            print("no restatement found for this concept in the returned window")
    except (urllib.error.URLError, KeyError, IndexError) as exc:
        print(f"EDGAR fetch failed ({exc}); skipping this demonstration")


if __name__ == "__main__":
    main()
