"""Vectorized production companion for ``core/signal_search.py``.

Requires ``pandas numpy``. The core file makes each point-in-time lookup
visible; this file shows the production form: sorted availability timestamps,
``merge_asof(direction='backward')``, and a structured experiment event for
every parameter choice. Store these events in MLflow, a versioned Parquet table,
or an append-only object store; a dashboard is not a substitute for the log.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def point_in_time_panel(prices: pd.DataFrame, filings: pd.DataFrame) -> pd.DataFrame:
    """Attach only filings available on each price date; never use ``nearest``."""
    return pd.merge_asof(
        prices.sort_values("date"), filings.sort_values("filed"), left_on="date",
        right_on="filed", by="ticker", direction="backward",
    )


def momentum(panel: pd.DataFrame, lookback_days: int, skip_days: int) -> pd.Series:
    """Same past-only momentum family as core, vectorized per ticker."""
    close = panel.groupby("ticker", sort=False)["adjusted_close"]
    return close.shift(skip_days) / close.shift(lookback_days) - 1.0


def log_variant(path: Path, params: dict[str, int], statistic: float | None) -> None:
    """Append one structured event per evaluated candidate, never a hand summary."""
    event = {"schema_version": 1, "family": "momentum", "params": params,
             "in_sample_ic": statistic, "code_path": "prod/pandas_search.py"}
    with path.open("a", encoding="utf-8") as output:
        output.write(json.dumps(event) + "\n")


def rank_ic(signal: pd.Series, forward_return: pd.Series) -> float:
    """Cross-sectional rank IC; production code groups this by rebalance date."""
    return float(signal.corr(forward_return, method="spearman"))


if __name__ == "__main__":
    print("Supply a point-in-time price/filing panel, then evaluate and log each grid row.")
