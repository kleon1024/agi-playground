"""Turn a score into a portfolio: cross-sectional ranking and the sizing ladder.

Stage 01 (running in parallel, not imported here) builds candidate signals from
point-in-time-only inputs and discloses a search log of every variant it
tried. This stage does not build a signal at all — it takes a raw score per
name per rebalance date and answers the question stage 01 hands off: how does
a score become a set of target weights? That translation is not a detail
bolted onto a signal. Two sizing rules applied to the exact same score produce
two different portfolios, with different risk, different turnover, and
different capacity — a different strategy, not a cosmetic variant of one.

To make that translation concrete with real numbers instead of synthetic
noise, this file borrows the mission's own already-declared, non-proprietary
momentum baseline (`mission.yaml`'s baseline #2: 12-month return skipping the
most recent month) purely as a stand-in score. This is a disclosed choice, not
a claim of a discovered edge — stage 01 owns signal search, and reusing a
signal already named as a public baseline avoids duplicating or pre-empting
that work. Prices come from `../../00-market-data/core/point_in_time.py`'s
`fetch_price_history`, so every score here traces to the same point-in-time
discipline stage 00 built, not a fresh, unaudited data path.

Two things this file is NOT trying to prove:

1. That momentum is a good signal. It is only a stand-in to exercise the
   ranking and sizing mechanism on real numbers.
2. That the resulting portfolios are tradeable. Every number this script
   prints is a paper portfolio: no transaction costs, no market-impact model,
   no capacity limit. Stage 04 (`04-cost-and-capacity`) is where the gap
   between this number and a tradeable one gets measured.

Run:  python cross_sectional_rank.py --range 3y --top-frac 0.1 --cap 0.10
"""

from __future__ import annotations

import argparse
import statistics
import sys
import urllib.error
from datetime import UTC, date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "00-market-data" / "core"))

from point_in_time import fetch_price_history  # our stage-00 fetcher, not re-derived

# --------------------------------------------------------------------------
# The universe and its sector map
#
# Thirty large, liquid US-listed names chosen for free-data availability and
# even sector coverage (five per sector), not as a recommendation of any
# security. The sector label attached to each ticker is TODAY's sector — a
# single static classification applied uniformly across the entire backtest
# window. That is exactly the trap stage 00 built its whole discipline around
# avoiding: a real point-in-time sector history would let a name's sector
# label change the day a reclassification took effect (index providers do
# this periodically), and using today's label for a rebalance date three
# years ago silently assumes the classification was already knowable then.
# Free sources do not hand you a point-in-time sector history the way a
# licensed vendor does (see stage 00's own "what prod/ still cannot do" note),
# so this stage names the gap instead of hiding it: every sector-neutrality
# number below is computed against a classification that is not point-in-time
# correct, and should be read with that caveat attached.
# --------------------------------------------------------------------------
UNIVERSE: dict[str, str] = {
    "AAPL": "tech", "MSFT": "tech", "GOOGL": "tech", "NVDA": "tech", "ORCL": "tech",
    "JPM": "financials", "BAC": "financials", "GS": "financials", "MS": "financials", "WFC": "financials",
    "JNJ": "healthcare", "PFE": "healthcare", "UNH": "healthcare", "ABBV": "healthcare", "MRK": "healthcare",
    "XOM": "energy", "CVX": "energy", "COP": "energy", "SLB": "energy", "EOG": "energy",
    "PG": "consumer", "KO": "consumer", "PEP": "consumer", "WMT": "consumer", "MCD": "consumer",
    "CAT": "industrials", "BA": "industrials", "HON": "industrials", "GE": "industrials", "UPS": "industrials",
}

MOMENTUM_LOOKBACK_DAYS = 252  # ~12 trading months
MOMENTUM_SKIP_DAYS = 21  # ~1 trading month, skipped to avoid short-term reversal


def _to_date(unix_ts: int) -> date:
    return datetime.fromtimestamp(unix_ts, tz=UTC).date()


def fetch_universe_closes(range_: str) -> tuple[list[date], dict[str, list[float]]]:
    """Fetch every ticker, then restrict to the calendar every ticker shares.

    A per-ticker close series is only comparable to another's on a date both
    actually traded. Intersecting rather than unioning keeps every downstream
    index aligned by position, so `trading_days[i]` means the same day for
    every ticker's close list without a second lookup.
    """
    per_ticker: dict[str, dict[date, float]] = {}
    for ticker in UNIVERSE:
        try:
            bars, _dividends, _splits = fetch_price_history(ticker, range_)
        except (urllib.error.URLError, KeyError, IndexError) as exc:
            print(f"skipping {ticker}: fetch failed ({exc})")
            continue
        per_ticker[ticker] = {
            _to_date(b.ts): (b.adjclose if b.adjclose is not None else b.close) for b in bars
        }

    common_days = set.intersection(*(set(d.keys()) for d in per_ticker.values()))
    trading_days = sorted(common_days)
    closes = {t: [d[day] for day in trading_days] for t, d in per_ticker.items()}
    return trading_days, closes


def monthly_rebalance_indices(trading_days: list[date]) -> list[int]:
    """Index of the last trading day of each calendar month.

    A monthly rebalance calendar is a business decision (how often the book
    turns over enough to justify recomputing weights), not a data artifact —
    stated here explicitly rather than left as an unexamined default.
    """
    indices = []
    for i, day in enumerate(trading_days):
        is_last_of_month = i + 1 == len(trading_days) or trading_days[i + 1].month != day.month
        if is_last_of_month:
            indices.append(i)
    return indices


def momentum_score(closes: list[float], idx: int) -> float | None:
    """12-month return skipping the most recent month, at `idx` in `closes`.

    Only ever reads `closes[j]` for `j <= idx`: no index past the rebalance
    date's own position is touched, so this score cannot see its own future
    even though the full price series has already been fetched into memory.
    """
    lookback_idx = idx - MOMENTUM_LOOKBACK_DAYS
    skip_idx = idx - MOMENTUM_SKIP_DAYS
    if lookback_idx < 0:
        return None
    return closes[skip_idx] / closes[lookback_idx] - 1.0


# --------------------------------------------------------------------------
# Cross-sectional transforms: why rank, not raw level
# --------------------------------------------------------------------------


def rank_percentile(scores: dict[str, float]) -> dict[str, float]:
    """Map raw scores to a percentile in (0, 1], independent of their scale.

    By construction, this distribution is uniform over any universe on every
    date: the best name is always exactly 1.0, the worst always 1/N, no
    matter whether the underlying scores that date span 2% or 40%. A raw
    score has no such guarantee — its scale and spread drift with the market
    regime, so a fixed weighting rule applied to raw levels implicitly
    reweights itself over time as the level distribution widens or narrows,
    whether or not that was the intended behavior.
    """
    ordered = sorted(scores, key=lambda k: scores[k])
    n = len(ordered)
    return {ticker: (i + 1) / n for i, ticker in enumerate(ordered)}


def centered_rank(scores: dict[str, float]) -> dict[str, float]:
    """Rank percentile re-centered to [-1, 1]: positive for the better half."""
    pct = rank_percentile(scores)
    return {t: 2 * p - 1 - 1 / len(scores) for t, p in pct.items()}


def cross_sectional_zscore(scores: dict[str, float]) -> dict[str, float]:
    values = list(scores.values())
    mu = statistics.mean(values)
    sigma = statistics.pstdev(values) or 1e-9
    return {t: (v - mu) / sigma for t, v in scores.items()}


# --------------------------------------------------------------------------
# The sizing ladder
#
# Every rule below is normalized, before any constraint is applied, to the
# same gross exposure (2.0: 100% long, 100% short) so that a difference in
# gross exposure measured AFTER constraints is attributable to the shape of
# the rule — how concentrated its raw weights are — and not to an arbitrary
# difference in how each rule happened to be scaled.
# --------------------------------------------------------------------------

TARGET_GROSS = 2.0


def _normalize_to_gross(raw: dict[str, float], target_gross: float = TARGET_GROSS) -> dict[str, float]:
    total_abs = sum(abs(w) for w in raw.values()) or 1e-9
    scale = target_gross / total_abs
    return {t: w * scale for t, w in raw.items()}


def equal_weight_decile(scores: dict[str, float], top_frac: float = 0.1) -> dict[str, float]:
    """Equal weight over the top `top_frac` of names, equal short over the
    bottom `top_frac`. Encodes the strongest possible belief about the
    signal: it carries information about ORDER at the extremes and nothing
    else — the 4th-best name is worth exactly as much as the 2nd-best, and
    everything outside the two tails is worth exactly zero.
    """
    ordered = sorted(scores, key=lambda k: scores[k])
    k = max(1, round(len(ordered) * top_frac))
    shorts, longs = ordered[:k], ordered[-k:]
    weights = {t: 1.0 / k for t in longs}
    weights.update({t: -1.0 / k for t in shorts})
    return weights


def rank_proportional(scores: dict[str, float]) -> dict[str, float]:
    """Weight proportional to centered cross-sectional rank, full universe.

    Encodes a softer belief than the decile rule: order matters everywhere,
    not just at the extremes, but the SIZE of a rank gap between two adjacent
    names is treated as meaningless — the 1st and 2nd best names are as far
    apart in weight as the 15th and 16th, because rank spacing is uniform by
    construction regardless of how the underlying scores are actually spaced.
    """
    return _normalize_to_gross(centered_rank(scores))


def signal_proportional(scores: dict[str, float]) -> dict[str, float]:
    """Weight proportional to the z-scored raw signal, full universe.

    Encodes the belief that the signal carries information about MAGNITUDE,
    not just order: a name whose raw score is far above the cross-sectional
    mean gets more conviction than one just barely above it, even if their
    ranks are adjacent. This is a stronger, more specific claim about the
    signal than rank-proportional makes, and it is only justified if the
    signal's scale genuinely reflects the strength of the expected effect —
    a claim that has to be checked, not assumed.
    """
    return _normalize_to_gross(cross_sectional_zscore(scores))


def volatility_scaled(scores: dict[str, float], trailing_vol: dict[str, float]) -> dict[str, float]:
    """Signal-proportional, then divided by each name's trailing realized
    volatility before renormalizing.

    Same conviction-by-magnitude belief as signal-proportional, plus a second
    belief: equal dollars of two names carrying equal signal conviction
    should not carry equal RISK. A volatile name moves the book's P&L more
    per dollar invested than a quiet one does, so this rule trades some
    conviction-following for risk parity across names — a real risk-
    management concern a research-only sizing rule can otherwise ignore.
    """
    z = cross_sectional_zscore(scores)
    raw = {t: z[t] / max(trailing_vol.get(t, 1e-6), 1e-6) for t in scores}
    return _normalize_to_gross(raw)


SIZING_RULES = {
    "equal_weight_decile": lambda scores, vol: equal_weight_decile(scores),
    "rank_proportional": lambda scores, vol: rank_proportional(scores),
    "signal_proportional": lambda scores, vol: signal_proportional(scores),
    "volatility_scaled": lambda scores, vol: volatility_scaled(scores, vol),
}


# --------------------------------------------------------------------------
# Constraints a real book carries: caps and sector neutrality
# --------------------------------------------------------------------------


def apply_position_cap(weights: dict[str, float], cap: float) -> dict[str, float]:
    """Clip every weight to +/- cap. Naive on purpose: the notional this clip
    removes from an over-cap name is simply discarded, not redistributed to
    any other name. `prod/pandas_lp_rank.py` expresses the identical cap as
    an explicit optimizer bound instead, and the difference in what survives
    is the whole point of that file.
    """
    return {t: max(-cap, min(cap, w)) for t, w in weights.items()}


def apply_sector_neutralization(weights: dict[str, float]) -> dict[str, float]:
    """Demean each sector's weights to force that sector's net exposure to
    zero. Applied AFTER the position cap, which means demeaning can push a
    name that was exactly at the cap back over it — this function does not
    re-check the cap, and the driver below measures how often that happens
    on real data rather than asserting it.
    """
    by_sector: dict[str, list[str]] = {}
    for t in weights:
        by_sector.setdefault(UNIVERSE[t], []).append(t)
    result = dict(weights)
    for members in by_sector.values():
        sector_mean = sum(weights[t] for t in members) / len(members)
        for t in members:
            result[t] = weights[t] - sector_mean
    return result


def apply_constraints(weights: dict[str, float], cap: float) -> tuple[dict[str, float], int]:
    capped = apply_position_cap(weights, cap)
    neutralized = apply_sector_neutralization(capped)
    cap_violations_after_neutralization = sum(1 for w in neutralized.values() if abs(w) > cap + 1e-9)
    return neutralized, cap_violations_after_neutralization


# --------------------------------------------------------------------------
# What a rebalance produces: turnover, concentration, and the paper return
# --------------------------------------------------------------------------


def turnover(current: dict[str, float], previous: dict[str, float]) -> float:
    """One-way turnover: half the sum of absolute weight changes, the
    standard convention that counts a $1 shift from one name to another as
    $1 traded, not $2.
    """
    all_tickers = set(current) | set(previous)
    return 0.5 * sum(abs(current.get(t, 0.0) - previous.get(t, 0.0)) for t in all_tickers)


def concentration_hhi(weights: dict[str, float]) -> float:
    """Herfindahl-Hirschman index over weights: higher means a smaller
    number of names account for most of the book's exposure.
    """
    return sum(w * w for w in weights.values())


def gross_exposure(weights: dict[str, float]) -> float:
    return sum(abs(w) for w in weights.values())


def period_return(weights: dict[str, float], closes: dict[str, list[float]], idx_now: int, idx_next: int) -> float:
    return sum(w * (closes[t][idx_next] / closes[t][idx_now] - 1.0) for t, w in weights.items())


def annualized_sharpe(period_returns: list[float], periods_per_year: int = 12) -> float:
    if len(period_returns) < 2:
        return 0.0
    mu = statistics.mean(period_returns)
    sigma = statistics.pstdev(period_returns) or 1e-9
    return (mu / sigma) * (periods_per_year ** 0.5)


def trailing_volatility(closes: list[float], idx: int, window: int = 60) -> float:
    """Annualized stdev of daily returns over the `window` trading days
    ending at `idx`, using only `closes[j]` for `j <= idx`.
    """
    start = max(1, idx - window + 1)
    rets = [closes[j] / closes[j - 1] - 1.0 for j in range(start, idx + 1) if closes[j - 1]]
    if len(rets) < 2:
        return 1e-6
    return statistics.pstdev(rets) * (252 ** 0.5)


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------


def run(range_: str, top_frac: float, cap: float) -> None:
    trading_days, closes = fetch_universe_closes(range_)
    tickers = list(closes)
    print(f"universe: {len(tickers)} names, {len(trading_days)} common trading days ({range_})")

    reb_indices = monthly_rebalance_indices(trading_days)
    usable = [i for i in reb_indices if i - MOMENTUM_LOOKBACK_DAYS >= 0 and i + 1 < len(trading_days)]
    print(f"usable rebalance dates: {len(usable)} "
          f"({trading_days[usable[0]]} to {trading_days[usable[-1]]})\n")

    # Illustrate why rank beats raw level: the raw score's own cross-sectional
    # scale at the first and last usable rebalance, from real fetched prices.
    first_scores = {t: momentum_score(closes[t], usable[0]) for t in tickers}
    last_scores = {t: momentum_score(closes[t], usable[-1]) for t in tickers}
    print("raw signal scale drifts across the window (rank distribution never does):")
    print(f"  {trading_days[usable[0]]}: mean={statistics.mean(first_scores.values()):+.3f} "
          f"stdev={statistics.pstdev(first_scores.values()):.3f}")
    print(f"  {trading_days[usable[-1]]}: mean={statistics.mean(last_scores.values()):+.3f} "
          f"stdev={statistics.pstdev(last_scores.values()):.3f}\n")

    last_snapshot: dict[str, dict[str, dict[str, float]]] = {}

    for rule_name, rule_fn in SIZING_RULES.items():
        for constrained in (False, True):
            prev_weights: dict[str, float] = {}
            turnovers, grosses, hhis, returns = [], [], [], []
            total_violations = 0
            for pos, idx in enumerate(usable):
                scores = {t: momentum_score(closes[t], idx) for t in tickers}
                vol = {t: trailing_volatility(closes[t], idx) for t in tickers}
                weights = rule_fn(scores, vol)
                if constrained:
                    weights, violations = apply_constraints(weights, cap)
                    total_violations += violations
                if pos > 0:
                    turnovers.append(turnover(weights, prev_weights))
                grosses.append(gross_exposure(weights))
                hhis.append(concentration_hhi(weights))
                if idx + 1 < len(trading_days):
                    returns.append(period_return(weights, closes, idx, idx + 1))
                prev_weights = weights
                if pos == len(usable) - 1:
                    last_snapshot.setdefault(rule_name, {})["constrained" if constrained else "raw"] = weights

            label = f"{rule_name:<22} {'constrained' if constrained else 'raw        '}"
            print(
                f"{label}  gross={statistics.mean(grosses):.2f}  "
                f"HHI={statistics.mean(hhis):.4f}  "
                f"turnover/mo={statistics.mean(turnovers):.3f}  "
                f"paper Sharpe={annualized_sharpe(returns):+.2f}"
                + (f"  cap-violations-after-sector-demean={total_violations}" if constrained else "")
            )

    print("\nlast-rebalance weight snapshot (constrained), for the widget's measured defaults:")
    for rule_name, states in last_snapshot.items():
        weights = states["constrained"]
        top = sorted(weights.items(), key=lambda kv: -kv[1])[:3]
        bottom = sorted(weights.items(), key=lambda kv: kv[1])[:3]
        print(f"  {rule_name}: top longs {top}, top shorts {bottom}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--range", default="3y")
    ap.add_argument("--top-frac", type=float, default=0.1, help="top/bottom fraction for equal_weight_decile")
    ap.add_argument("--cap", type=float, default=0.10, help="per-name position cap as a fraction of the book")
    args = ap.parse_args()
    run(args.range, args.top_frac, args.cap)


if __name__ == "__main__":
    main()
