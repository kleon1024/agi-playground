"""From-scratch transaction-cost and capacity model: what a signal is worth
once it has to trade.

A validated signal (stage 03) says a strategy's returns are real, not a
multiple-testing artifact. It says nothing about how much money can be put
behind it, because every dollar traded pays three different kinds of cost,
and one of those three grows the wrong way as the book gets bigger:

1. **Commission** — a broker's fee, close to linear in dollars traded. Doubling
   the trade roughly doubles the commission. Boring, and not where capacity
   comes from.
2. **Spread** — the bid-ask toll paid just to cross the market, roughly a
   fixed number of basis points per dollar traded regardless of size, for
   trades that stay small relative to the day's volume. Also not where
   capacity comes from.
3. **Market impact** — the price concession a large order has to offer the
   market to get filled. This is the one that misbehaves: the widely used
   *square-root model* says impact scales with the square root of how much of
   a day's volume the trade represents, not linearly with it. Square root
   grows slower than linear, so impact cost *per dollar traded* still rises
   with size — just sublinearly. That is enough, once turnover compounds a
   per-trade cost into an annual one, to turn a strategy that is profitable
   on paper into one that loses money once it is sized up.

The square-root model is an empirical regularity fitted to particular markets
and periods, not a law of physics. Even within the literature the exponent is
debated: Almgren, Thum, Hauptmann, and Li (2005), "Direct Estimation of
Equity Market Impact," Risk 18(7), fit a large Citigroup US-equity desk
dataset and found a closer-to-3/5 power law for temporary impact, not a pure
square root. Toth, Lemperiere, Deremble, de Lataillade, Kockelkoren, and
Bouchaud (2011), "Anomalous Price Impact and the Critical Nature of Liquidity
in Financial Markets," Physical Review X 1, 021006, found approximately
square-root scaling more broadly across many markets and give a theoretical
account of why. This module uses the square-root form because it is the one
most production desks reach for first; the coefficient in front of it (`Y`
below) is *assumed*, not fitted from this repository's data, because this
repository has no execution fills to fit it from. `prod/` shows the fitting
workflow a real desk runs instead of assuming.

Two of this file's three inputs to the impact model are real, measured
numbers: average daily dollar volume (`ADV`) and realized daily volatility,
both computed from the same public Yahoo Finance chart endpoint stage 00
uses, for whatever ticker `--ticker` names. The third input, the impact
coefficient `Y`, is a disclosed literature-informed assumption. That split —
real liquidity and volatility, assumed impact coefficient — is exactly what
the evidence-boundary section of this stage's README states plainly instead
of hiding.

Run:  python cost_capacity.py --ticker AAPL --range 2y --turnover 6
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import urllib.error
import urllib.request

_HEADERS = {"User-Agent": "agi-playground research contact@example.com"}
_TRADING_DAYS_PER_YEAR = 252
_REBALANCES_PER_YEAR = 12  # assumed monthly rebalance cadence, disclosed below

# --- Assumed cost-stack parameters (not fitted; see module docstring) -------
COMMISSION_BPS = 0.5  # one-way, institutional bulk-commission territory
SPREAD_BPS_LARGE_CAP = 2.0  # half-spread paid crossing the market, high-ADV name
SPREAD_BPS_SMALLER_CAP = 8.0  # half-spread for a lower-ADV, wider-quoted name
SPREAD_TIER_ADV_THRESHOLD = 1e9  # $1B/day ADV: crude large-cap/smaller-cap cut
IMPACT_COEFFICIENT_Y = 0.6  # middle of the range the cited literature reports


# --------------------------------------------------------------------------
# 1. Real, measured inputs: liquidity and volatility
# --------------------------------------------------------------------------


def fetch_daily_bars(ticker: str, range_: str = "2y") -> tuple[list[float], list[float]]:
    """Daily close and volume from Yahoo's public chart endpoint. No API key.

    Same endpoint stage 00 uses for prices; this stage additionally needs
    `volume`, which stage 00's panel does not carry, so it is pulled here
    directly rather than assumed or borrowed from another stage's file.
    """
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?range={range_}&interval=1d"
    request = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.load(response)
    result = payload["chart"]["result"][0]
    quote = result["indicators"]["quote"][0]
    closes, volumes = [], []
    for c, v in zip(quote["close"], quote["volume"]):
        if c is not None and v is not None:
            closes.append(float(c))
            volumes.append(float(v))
    return closes, volumes


def realized_daily_vol(closes: list[float]) -> float:
    """Standard deviation of daily log returns — the `sigma` the impact model
    needs, measured from real prices rather than assumed."""
    log_returns = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
    return statistics.pstdev(log_returns)


def average_daily_dollar_volume(closes: list[float], volumes: list[float]) -> float:
    """Mean of close * volume across the window — real average daily volume
    in dollars, the `ADV` the participation rate is measured against."""
    return statistics.mean(c * v for c, v in zip(closes, volumes))


# --------------------------------------------------------------------------
# 2. The cost stack: three pieces, three different growth rates
# --------------------------------------------------------------------------


def spread_bps_for(adv_dollars: float) -> float:
    """Crude two-tier assumption: deeper daily volume gets a tighter assumed
    spread. A real desk would use its own quoted-spread history per name
    instead of a two-bucket rule; this is a disclosed simplification."""
    return SPREAD_BPS_LARGE_CAP if adv_dollars >= SPREAD_TIER_ADV_THRESHOLD else SPREAD_BPS_SMALLER_CAP


def impact_cost_frac(participation_rate: float, daily_vol: float, y: float = IMPACT_COEFFICIENT_Y) -> float:
    """Square-root impact model: cost, as a fraction of price, of trading a
    given share of one day's volume. `participation_rate` is trade notional
    divided by ADV; `daily_vol` is the measured daily volatility. Doubling
    the trade (participation_rate) multiplies impact cost by sqrt(2) =~ 1.41,
    not by 2 — sublinear, but still strictly increasing, which is the whole
    story of this stage."""
    return y * daily_vol * math.sqrt(max(0.0, participation_rate))


def per_trade_cost_frac(participation_rate: float, daily_vol: float, adv_dollars: float) -> dict[str, float]:
    """One rebalance's cost, broken into its three pieces, each as a
    fraction of the notional traded in that single rebalance."""
    commission = COMMISSION_BPS / 10_000
    spread = spread_bps_for(adv_dollars) / 10_000
    impact = impact_cost_frac(participation_rate, daily_vol)
    return {"commission": commission, "spread": spread, "impact": impact, "total": commission + spread + impact}


# --------------------------------------------------------------------------
# 3. Turnover: the multiplier that makes a per-trade cost an annual drag
# --------------------------------------------------------------------------


def annual_cost_frac(book_size: float, turnover_annual: float, adv_dollars: float, daily_vol: float) -> dict[str, float]:
    """Net annual cost as a fraction of book value.

    Stage 02's cross-sectional ranking produces target weights and, from
    rebalance to rebalance, a turnover series: the fraction of the book that
    actually trades each time the ranking is refreshed. `turnover_annual`
    here is that series's annual sum — e.g. 6.0 means the book's full value
    turns over six times a year, one way.

    We assume a monthly rebalance cadence (12/year), so each rebalance trades
    `turnover_annual / 12` of book value, and we assume — deliberately, and
    conservatively for the impact term — that this whole trade executes
    within a single day's volume rather than being sliced across several
    days, which is what a real execution algorithm would do specifically to
    reduce this cost. That simplification pushes the impact estimate up, not
    down.

    Each rebalance's traded notional sets its participation rate against
    ADV, so `annual_cost_frac` is not simply `turnover_annual * a constant`:
    turnover raises the annual cost two ways at once — directly, as more
    trades happen, and indirectly, because each of those trades is bigger
    relative to ADV, which pushes the impact term up along its square root.
    """
    monthly_traded_notional = book_size * turnover_annual / _REBALANCES_PER_YEAR
    participation = monthly_traded_notional / adv_dollars if adv_dollars > 0 else float("inf")
    per_trade = per_trade_cost_frac(participation, daily_vol, adv_dollars)
    return {
        **per_trade,
        "participation_rate": participation,
        "annual_commission": turnover_annual * per_trade["commission"],
        "annual_spread": turnover_annual * per_trade["spread"],
        "annual_impact": turnover_annual * per_trade["impact"],
        "annual_total": turnover_annual * per_trade["total"],
    }


# --------------------------------------------------------------------------
# 4. The capacity curve
# --------------------------------------------------------------------------


def capacity_curve(
    gross_return_annual: float,
    turnover_annual: float,
    adv_dollars: float,
    daily_vol: float,
    book_sizes: list[float],
) -> list[dict[str, float]]:
    """Net return, and net dollar return, at every candidate book size.

    Net *percentage* return falls monotonically as the book grows, because
    cost only ever goes up. Net *dollar* return — book size times net
    percentage return — rises while the book is small enough that costs are
    negligible, peaks, then falls and eventually turns negative: the
    "capacity curve" this stage's opening question is about.
    """
    rows = []
    for book in book_sizes:
        costs = annual_cost_frac(book, turnover_annual, adv_dollars, daily_vol)
        net_return_pct = gross_return_annual - costs["annual_total"]
        rows.append(
            {
                "book_size": book,
                "participation_rate": costs["participation_rate"],
                "annual_cost_frac": costs["annual_total"],
                "net_return_pct": net_return_pct,
                "net_dollar_return": book * net_return_pct,
            }
        )
    return rows


def find_capacity(curve: list[dict[str, float]]) -> dict[str, float | None]:
    """Two different answers to "how big can this get":

    - `peak_book_size`: the book size that maximizes total net dollar
      return — beyond this point every *additional* dollar deployed adds
      zero or negative profit, even though the strategy overall may still be
      net profitable a bit further out. This is "marginal net return hits
      zero," and it is the number this stage's opening question is really
      asking for: the size beyond which putting in more money stops helping.
    - `breakeven_book_size`: the larger book size where cumulative net
      dollar return itself crosses zero — the strategy has stopped making
      money at all, not just stopped making more of it.
    """
    peak = max(curve, key=lambda r: r["net_dollar_return"])
    breakeven = next((r["book_size"] for r in curve if r["net_dollar_return"] <= 0 and r["book_size"] > peak["book_size"]), None)
    return {
        "peak_book_size": peak["book_size"],
        "peak_net_dollar_return": peak["net_dollar_return"],
        "breakeven_book_size": breakeven,
    }


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------


def _book_size_sweep(adv_dollars: float) -> list[float]:
    """A log-ish sweep from a small fraction of ADV up to ~1000x ADV, wide
    enough that every ticker and turnover combination this stage prints has
    both its peak and its breakeven land inside the sweep."""
    multipliers = [0.25, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 400, 700, 1000]
    return [adv_dollars * m for m in multipliers]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", default="AAPL")
    ap.add_argument("--range", default="2y")
    ap.add_argument("--gross-return", type=float, default=0.12, help="paper annual return, e.g. 0.12 for 12%")
    ap.add_argument("--turnover", type=float, default=6.0, help="annual one-way turnover, in multiples of book value")
    args = ap.parse_args()

    try:
        closes, volumes = fetch_daily_bars(args.ticker, args.range)
    except (urllib.error.URLError, KeyError, IndexError) as exc:
        print(f"price/volume fetch failed ({exc}); cannot compute a real ADV or volatility for {args.ticker}")
        return

    adv = average_daily_dollar_volume(closes, volumes)
    vol = realized_daily_vol(closes)
    print(f"=== {args.ticker}: measured inputs over {args.range} ({len(closes)} bars) ===")
    print(f"average daily dollar volume (ADV): ${adv:,.0f}")
    print(f"realized daily volatility: {vol:.4%}")
    print(f"assumed impact coefficient Y: {IMPACT_COEFFICIENT_Y}  (see module docstring)")
    print(f"assumed spread: {spread_bps_for(adv):.1f} bps   assumed commission: {COMMISSION_BPS} bps")

    print(f"\n=== cost stack at a $10M book, {args.turnover:.1f}x annual turnover ===")
    sample = annual_cost_frac(10_000_000, args.turnover, adv, vol)
    print(f"participation rate per rebalance: {sample['participation_rate']:.4%}")
    print(f"per-trade cost (bps): commission {sample['commission'] * 10_000:.2f}  "
          f"spread {sample['spread'] * 10_000:.2f}  impact {sample['impact'] * 10_000:.2f}")
    print(f"annualized (x{args.turnover:.1f} turnover): commission {sample['annual_commission']:.4%}  "
          f"spread {sample['annual_spread']:.4%}  impact {sample['annual_impact']:.4%}  "
          f"total {sample['annual_total']:.4%}")

    curve = capacity_curve(args.gross_return, args.turnover, adv, vol, _book_size_sweep(adv))
    capacity = find_capacity(curve)
    print(f"\n=== capacity curve: {args.gross_return:.1%} gross, {args.turnover:.1f}x turnover ===")
    print(f"{'book size':>16} {'participation':>14} {'net return':>12} {'net $ return':>16}")
    for row in curve:
        print(
            f"${row['book_size']:>14,.0f} {row['participation_rate']:>13.2%} "
            f"{row['net_return_pct']:>11.2%} ${row['net_dollar_return']:>14,.0f}"
        )
    print(f"\npeak (marginal net return = 0): ${capacity['peak_book_size']:,.0f} book, "
          f"net dollar return ${capacity['peak_net_dollar_return']:,.0f}/year")
    if capacity["breakeven_book_size"] is not None:
        print(f"breakeven (total net return = 0): ${capacity['breakeven_book_size']:,.0f} book")
    else:
        print("breakeven not reached within this sweep")


if __name__ == "__main__":
    main()
