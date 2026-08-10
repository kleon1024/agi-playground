"""Candidate signal construction and search-log discipline, from scratch.

Stage 00 answered "what was actually knowable on this date?" for prices and
fundamentals. This stage asks the next question: given that honest panel and
an idea, how many variants of that idea are you allowed to try before the
best one you find is guaranteed to look good whether or not it is real?

With enough variants, a good-looking in-sample statistic is the *expected*
outcome of search, not evidence about the underlying signal. The only thing
that restores meaning to a reported number is knowing how many variants were
tried — hence `search_log.jsonl`, appended to automatically by
`evaluate_variant` for every variant this file ever scores against real data.
Nobody has to remember to log a variant; the harness cannot compute a
real-data statistic without logging it. Stage 03 will consume this log's line
count as the N in a deflated Sharpe ratio.

Three signal families, each with a small grid of genuine free parameters:

* momentum       — trailing total return, skipping the most recent month(s)
* low_volatility — negative realized volatility of trailing monthly returns
* value_book_to_market — book equity over market equity (book-to-market)

All three reuse `../00-market-data/core/point_in_time.py` directly: the
adjusted-close price reconstruction, and the raw EDGAR facts a "latest known
value as of date X" lookup is built from here. Every signal at every
rebalance date only reads panel history at or before that date, by
construction of the as-of lookup below — the same discipline stage 00 built,
applied to a cross-section of names and a search grid instead of one ticker.

Universe: ten large, continuously-listed companies (Apple, Microsoft,
Johnson & Johnson, Procter & Gamble, Coca-Cola, Exxon Mobil, JPMorgan Chase,
Walmart, Pfizer, Cisco). None was delisted, merged, or renamed during the
study window, so this stage can borrow stage 00's point-in-time functions
without also re-solving stage 00's survivorship problem — that problem is
already declared out of scope for free data in stage 00's README, and a
ten-name hand-picked universe does not escape it either; see the README's
evidence-boundary section.

Run:  python signal_search.py --range 5y --permutations 300
"""

from __future__ import annotations

import argparse
import bisect
import itertools
import json
import math
import random
import sys
import urllib.error
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "00-market-data" / "core"))
from point_in_time import (
    Fact,
    fetch_edgar_concept,
    fetch_price_history,
    reconstruct_adjusted_close,
)

UNIVERSE: list[tuple[str, int]] = [
    ("AAPL", 320193), ("MSFT", 789019), ("JNJ", 200406), ("PG", 80424),
    ("KO", 21344), ("XOM", 34088), ("JPM", 19617), ("WMT", 104169),
    ("PFE", 78003), ("CSCO", 858877),
]

# Equity is filed under different XBRL tags depending on whether a company has
# noncontrolling interests to net out. This is a real inconsistency this
# universe surfaced (Procter & Gamble 404s on the plain tag); it is not a bug
# in this stage's fetch code, and hard-coding one tag would have silently
# dropped one-tenth of the universe.
EQUITY_TAGS = ("StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest")

MIN_NAMES_PER_DATE = 5  # cross-section floor below which a correlation is noise, not a statistic
SCHEMA_VERSION = 1


@dataclass
class TickerPanel:
    ticker: str
    prices: list[tuple[date, float]]  # (calendar date, point-in-time-adjusted close), sorted
    equity: list[tuple[date, float]]  # (filed date, stockholders' equity), sorted by filed date
    shares: list[tuple[date, float]]  # (filed date, shares outstanding), sorted by filed date


@dataclass
class Variant:
    family: str
    params: dict[str, int]

    @property
    def key(self) -> str:
        return self.family + "/" + ",".join(f"{k}={v}" for k, v in sorted(self.params.items()))


# --------------------------------------------------------------------------
# Data acquisition — reuses stage 00 directly
# --------------------------------------------------------------------------


def _to_date(ts: int) -> date:
    return datetime.fromtimestamp(ts, tz=UTC).date()


def fetch_ticker_panel(ticker: str, cik: int, range_: str) -> TickerPanel:
    bars, dividends, _splits = fetch_price_history(ticker, range_)
    adj_close = reconstruct_adjusted_close(bars, dividends)
    prices = sorted(zip((_to_date(b.ts) for b in bars), adj_close))

    equity_facts: list[Fact] = []
    for tag in EQUITY_TAGS:
        try:
            equity_facts = fetch_edgar_concept(cik, tag)
            if equity_facts:
                break
        except urllib.error.HTTPError:
            continue  # this company reports the concept under the other tag

    shares_facts = fetch_edgar_concept(cik, "EntityCommonStockSharesOutstanding", taxonomy="dei")

    # Collapse to (filed date, value), keeping the point-in-time question this
    # stage cares about ("what was the most recently filed number by date X")
    # rather than stage 00's per-fiscal-period question. Same source data,
    # a different as-of query.
    equity = sorted({(f.filed, f.value) for f in equity_facts})
    shares = sorted({(f.filed, f.value) for f in shares_facts})
    return TickerPanel(ticker=ticker, prices=prices, equity=equity, shares=shares)


def fetch_universe(range_: str, universe: list[tuple[str, int]] = UNIVERSE) -> dict[str, TickerPanel]:
    panels: dict[str, TickerPanel] = {}
    for ticker, cik in universe:
        try:
            panels[ticker] = fetch_ticker_panel(ticker, cik, range_)
        except (urllib.error.URLError, KeyError, IndexError) as exc:
            print(f"  skipping {ticker}: fetch failed ({exc})")
    return panels


# --------------------------------------------------------------------------
# As-of lookups — the one mechanism every signal family is built from
# --------------------------------------------------------------------------


def as_of(series: list[tuple[date, float]], as_of_date: date) -> tuple[float, int] | tuple[None, None]:
    """Latest (value, age_in_days) in a (date, value) series at or before as_of_date.

    This is stage 00's backward as-of join (`point_in_time_value`, and
    `pandas.merge_asof(..., direction="backward")` in its prod/ counterpart),
    reused for two different sources here: for prices it answers "what did the
    market last print by this date", for fundamentals "what was the most
    recently filed number by this date". Same mechanism, and the same bug is
    available if you get it backward: use `bisect_right` wrong, or sort by
    fiscal period instead of filed date, and a fact that had not been filed
    yet leaks into a signal computed on this date.
    """
    dates = [d for d, _ in series]
    idx = bisect.bisect_right(dates, as_of_date) - 1
    if idx < 0:
        return None, None
    value_date, value = series[idx]
    return value, (as_of_date - value_date).days


def month_end_dates(start: date, end: date) -> list[date]:
    out = []
    y, m = start.year, start.month
    while date(y, m, 1) <= end:
        last_day = date(y + (1 if m == 12 else 0), 1 if m == 12 else m + 1, 1) - timedelta(days=1)
        if start <= last_day <= end:
            out.append(last_day)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


# --------------------------------------------------------------------------
# Signal families and their free-parameter grids
# --------------------------------------------------------------------------


def momentum_variants() -> list[Variant]:
    # Six lookbacks x three skip windows = 18 variants from two free
    # parameters. (12, 1) is the field's popularity baseline named in this
    # mission's mission.yaml; it is one point in this grid, not privileged.
    return [
        Variant("momentum", {"lookback_months": lb, "skip_months": sk})
        for lb, sk in itertools.product((3, 6, 9, 12, 18, 24), (0, 1, 2))
    ]


def low_volatility_variants() -> list[Variant]:
    return [Variant("low_volatility", {"window_months": w}) for w in (6, 12, 18, 24, 36)]


def value_variants() -> list[Variant]:
    # A staleness cap is a real, defensible free parameter: how old a filed
    # book-equity or shares figure is allowed to be before you refuse to use
    # it. Three caps on each of two facts = nine more variants.
    return [
        Variant("value_book_to_market", {"equity_staleness_days": ec, "shares_staleness_days": sc})
        for ec, sc in itertools.product((180, 365, 730), (180, 365, 730))
    ]


def all_variants() -> list[Variant]:
    return momentum_variants() + low_volatility_variants() + value_variants()


def signal_at(variant: Variant, panel: TickerPanel, rebalance_dates: list[date], i: int) -> float | None:
    """One signal family's value for one ticker at rebalance_dates[i], or None
    if the panel does not yet have enough history to compute it."""
    today = rebalance_dates[i]
    price_today, _ = as_of(panel.prices, today)
    if price_today is None:
        return None

    if variant.family == "momentum":
        lb, sk = variant.params["lookback_months"], variant.params["skip_months"]
        j_end, j_start = i - sk, i - sk - lb
        if j_start < 0:
            return None
        p_end, _ = as_of(panel.prices, rebalance_dates[j_end])
        p_start, _ = as_of(panel.prices, rebalance_dates[j_start])
        if not p_end or not p_start:
            return None
        return p_end / p_start - 1.0

    if variant.family == "low_volatility":
        w = variant.params["window_months"]
        if i - w < 0:
            return None
        prices = []
        for j in range(i - w, i + 1):
            p, _ = as_of(panel.prices, rebalance_dates[j])
            if p is None:
                return None
            prices.append(p)
        rets = [prices[k] / prices[k - 1] - 1.0 for k in range(1, len(prices))]
        if len(rets) < 2:
            return None
        mean = sum(rets) / len(rets)
        var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
        return -math.sqrt(var)  # negated: lower realized vol -> higher signal

    if variant.family == "value_book_to_market":
        equity, equity_age = as_of(panel.equity, today)
        shares, shares_age = as_of(panel.shares, today)
        if equity is None or shares is None or shares <= 0:
            return None
        if equity_age > variant.params["equity_staleness_days"]:
            return None
        if shares_age > variant.params["shares_staleness_days"]:
            return None
        return equity / (price_today * shares)

    raise ValueError(f"unknown signal family: {variant.family}")


# --------------------------------------------------------------------------
# Statistics: pooled cross-sectional information coefficient
# --------------------------------------------------------------------------


def _rank(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda k: values[k])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1
    return ranks


def spearman_ic(signals: list[float], forward_returns: list[float]) -> float | None:
    n = len(signals)
    if n < 3:
        return None
    rx, ry = _rank(signals), _rank(forward_returns)
    mean_x, mean_y = sum(rx) / n, sum(ry) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(rx, ry))
    var_x = sum((x - mean_x) ** 2 for x in rx)
    var_y = sum((y - mean_y) ** 2 for y in ry)
    denom = math.sqrt(var_x * var_y)
    return cov / denom if denom else None


def build_forward_returns(panels: dict[str, TickerPanel], rebalance_dates: list[date]) -> list[dict[str, float]]:
    """forward_returns[i][ticker] = return from rebalance_dates[i] to [i+1].

    Computed once, shared by every signal family: the label a signal is
    scored against does not depend on which family produced the signal.
    """
    out: list[dict[str, float]] = []
    for i in range(len(rebalance_dates) - 1):
        row = {}
        for ticker, panel in panels.items():
            p0, _ = as_of(panel.prices, rebalance_dates[i])
            p1, _ = as_of(panel.prices, rebalance_dates[i + 1])
            if p0 and p1:
                row[ticker] = p1 / p0 - 1.0
        out.append(row)
    out.append({})  # no forward return defined for the last rebalance date
    return out


def build_variant_signals(
    variant: Variant, panels: dict[str, TickerPanel], rebalance_dates: list[date]
) -> list[dict[str, float]]:
    out: list[dict[str, float]] = []
    for i in range(len(rebalance_dates)):
        row = {}
        for ticker, panel in panels.items():
            v = signal_at(variant, panel, rebalance_dates, i)
            if v is not None:
                row[ticker] = v
        out.append(row)
    return out


def evaluate(
    signals_by_date: list[dict[str, float]],
    forward_returns_by_date: list[dict[str, float]],
    min_names: int = MIN_NAMES_PER_DATE,
) -> tuple[float | None, int, int]:
    """Mean pooled cross-sectional Spearman IC across dates, equal-weighted
    per date. Returns (mean_ic, n_dates_used, n_obs_pooled)."""
    ics: list[float] = []
    n_obs = 0
    for signals, returns in zip(signals_by_date, forward_returns_by_date):
        names = sorted(set(signals) & set(returns))
        if len(names) < min_names:
            continue
        ic = spearman_ic([signals[n] for n in names], [returns[n] for n in names])
        if ic is not None:
            ics.append(ic)
            n_obs += len(names)
    if not ics:
        return None, 0, 0
    return sum(ics) / len(ics), len(ics), n_obs


def permute_forward_returns(
    forward_returns_by_date: list[dict[str, float]], rng: random.Random
) -> list[dict[str, float]]:
    """Shuffle which ticker's forward return goes with which ticker, within
    each date. This destroys any real relationship between a signal and the
    return that follows it while preserving each date's actual cross-section
    of returns — the correct null for a cross-sectional information
    coefficient, mirroring `BacktestOverfit`'s use of independent noise draws
    but applied to a search grid instead of an unbounded number of tries.
    """
    out = []
    for row in forward_returns_by_date:
        names = list(row.keys())
        values = [row[n] for n in names]
        rng.shuffle(values)
        out.append(dict(zip(names, values)))
    return out


# --------------------------------------------------------------------------
# The instrumented search harness
# --------------------------------------------------------------------------


def log_variant(log_path: Path, entry: dict) -> None:
    """The only way a variant's real-data statistic gets computed and kept is
    through this function — see `run_search`. There is no code path that
    scores a variant against real data without appending it here."""
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
        fh.flush()


def run_search(
    panels: dict[str, TickerPanel],
    rebalance_dates: list[date],
    forward_returns_by_date: list[dict[str, float]],
    log_path: Path,
    range_arg: str,
) -> list[tuple[Variant, float | None, int, int]]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("")  # fresh log for this run; see README on why
    results = []
    for variant in all_variants():
        signals = build_variant_signals(variant, panels, rebalance_dates)
        ic, n_dates, n_obs = evaluate(signals, forward_returns_by_date)
        entry = {
            "schema_version": SCHEMA_VERSION,
            "stage": "03-quantitative-research/signal-research",
            "family": variant.family,
            "params": variant.params,
            "universe_size": len(panels),
            "n_dates": n_dates,
            "n_obs": n_obs,
            "in_sample_ic": ic,
            "data_range": range_arg,
            "evaluated_at": datetime.now(tz=UTC).isoformat(timespec="seconds"),
            "code_path": "core/signal_search.py",
        }
        log_variant(log_path, entry)
        results.append((variant, ic, n_dates, n_obs))
    return results


def run_permutation_null(
    panels: dict[str, TickerPanel],
    rebalance_dates: list[date],
    forward_returns_by_date: list[dict[str, float]],
    n_permutations: int,
    seed: int,
) -> list[float]:
    """Best-of-grid IC under a null where every signal is real but no signal
    has any true relationship to the return that follows it, replicated
    `n_permutations` times. These replicates are diagnostic, not new signal
    variants under research — they are deliberately not written to
    search_log.jsonl, so the log's line count keeps meaning "real candidate
    variants tried," not "every computation this file ever ran."
    """
    signals_by_variant = {v.key: build_variant_signals(v, panels, rebalance_dates) for v in all_variants()}
    rng = random.Random(seed)
    best_per_replicate = []
    for _ in range(n_permutations):
        permuted = permute_forward_returns(forward_returns_by_date, rng)
        best = None
        for signals in signals_by_variant.values():
            ic, _, _ = evaluate(signals, permuted)
            if ic is not None and (best is None or ic > best):
                best = ic
        if best is not None:
            best_per_replicate.append(best)
    return best_per_replicate


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--range", default="5y", dest="range_")
    ap.add_argument("--permutations", type=int, default=300)
    # Fixed only so this script's permutation draws reproduce across runs on
    # the same data pull, not chosen to land the demonstration in a flattering
    # regime — the point of this chapter is the opposite of that kind of tuning.
    ap.add_argument("--seed", type=int, default=20260727)
    ap.add_argument("--log-path", default=str(Path(__file__).resolve().parents[1] / "runs" / "search_log.jsonl"))
    args = ap.parse_args()

    print(f"=== fetching {len(UNIVERSE)}-name universe, range={args.range_} ===")
    panels = fetch_universe(args.range_)
    print(f"panels fetched: {len(panels)}/{len(UNIVERSE)}")
    if len(panels) < MIN_NAMES_PER_DATE:
        print("too few names fetched to form a cross-section; aborting")
        return

    starts = [p.prices[0][0] for p in panels.values()]
    ends = [p.prices[-1][0] for p in panels.values()]
    rebalance_dates = month_end_dates(max(starts), min(ends))
    print(f"rebalance dates: {len(rebalance_dates)} ({rebalance_dates[0]} .. {rebalance_dates[-1]})")

    forward_returns_by_date = build_forward_returns(panels, rebalance_dates)

    print(f"\n=== searching {len(all_variants())} variants (momentum={len(momentum_variants())}, "
          f"low_volatility={len(low_volatility_variants())}, value={len(value_variants())}) ===")
    log_path = Path(args.log_path)
    results = run_search(panels, rebalance_dates, forward_returns_by_date, log_path, args.range_)
    scored = [(v, ic, nd, no) for v, ic, nd, no in results if ic is not None]
    if not scored:
        print("no variant produced a scoreable statistic; aborting")
        return
    best_variant, best_ic, best_nd, best_no = max(scored, key=lambda r: r[1])
    print(f"best in-sample IC: {best_ic:.4f}  ({best_variant.key}, n_dates={best_nd}, n_obs={best_no})")
    print(f"search log written: {log_path}  ({len(results)} variants, every one logged)")

    print(f"\n=== permutation null: {args.permutations} replicates, seed={args.seed} ===")
    null_best = run_permutation_null(panels, rebalance_dates, forward_returns_by_date, args.permutations, args.seed)
    null_best.sort()
    n = len(null_best)
    mean_null = sum(null_best) / n
    p_value = sum(1 for x in null_best if x >= best_ic) / n
    print(f"null best-of-grid IC: mean={mean_null:.4f}  "
          f"min={null_best[0]:.4f}  median={null_best[n // 2]:.4f}  max={null_best[-1]:.4f}")
    print(f"real best-of-grid IC {best_ic:.4f} vs null: permutation p-value = {p_value:.3f} "
          f"(fraction of {n} null replicates whose own best-of-grid IC matched or beat it)")


if __name__ == "__main__":
    main()
