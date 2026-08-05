"""What the position cap actually costs: concentration vs turnover vs Sharpe.

Stage 02's recorded run compared sizing rules at one cap (0.10). This script
fetches the universe once and sweeps the cap across five values for two
rules, so the three-way trade — concentration (HHI), turnover, and paper
Sharpe — is a measured curve instead of a single point. It also counts the
cap violations the stage's `apply_constraints` reveals: sector demeaning can
push a name that was exactly at the cap back over it, and the count is a
function of the cap.

Everything is imported from the stage's core; only the sweep is new.

Run:
    uv run python core/cap_sweep.py
"""

from __future__ import annotations

import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))

from cross_sectional_rank import (
    MOMENTUM_LOOKBACK_DAYS,
    SIZING_RULES,
    annualized_sharpe,
    apply_constraints,
    concentration_hhi,
    fetch_universe_closes,
    gross_exposure,
    momentum_score,
    monthly_rebalance_indices,
    period_return,
    trailing_volatility,
    turnover,
)

CAPS = (0.05, 0.10, 0.25, 0.50, 1.0)
RULES = ("rank_proportional", "signal_proportional")


def main() -> None:
    trading_days, closes = fetch_universe_closes("3y")
    tickers = list(closes)
    reb_indices = monthly_rebalance_indices(trading_days)
    usable = [i for i in reb_indices if i - MOMENTUM_LOOKBACK_DAYS >= 0 and i + 1 < len(trading_days)]
    print(f"universe: {len(tickers)} names, {len(usable)} usable rebalances")

    for rule_name in RULES:
        rule_fn = SIZING_RULES[rule_name]
        print(f"\n== {rule_name} ==")
        print(f"{'cap':>6} {'gross':>6} {'HHI':>8} {'turnover/mo':>11} {'paper Sharpe':>12} {'cap violations':>14}")
        for cap in CAPS:
            prev: dict[str, float] = {}
            turnovers: list[float] = []
            hhis: list[float] = []
            grosses: list[float] = []
            returns: list[float] = []
            violations = 0
            for pos, idx in enumerate(usable):
                scores = {t: momentum_score(closes[t], idx) for t in tickers}
                vol = {t: trailing_volatility(closes[t], idx) for t in tickers}
                weights, v = apply_constraints(rule_fn(scores, vol), cap)
                violations += v
                if pos > 0:
                    turnovers.append(turnover(weights, prev))
                grosses.append(gross_exposure(weights))
                hhis.append(concentration_hhi(weights))
                if idx + 1 < len(trading_days):
                    returns.append(period_return(weights, closes, idx, idx + 1))
                prev = weights
            print(
                f"{cap:>6.2f} {statistics.mean(grosses):>6.2f} {statistics.mean(hhis):>8.4f} "
                f"{statistics.mean(turnovers):>11.3f} {annualized_sharpe(returns):>+12.2f} "
                f"{violations:>14}"
            )


if __name__ == "__main__":
    main()
