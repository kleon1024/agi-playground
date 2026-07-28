"""Render a contract-owned quantitative tearsheet from a metrics artifact.

The verdict remains owned by ``core/report.py``. This production surface adds
pandas aggregation, drawdown dates, regime tables, and a matplotlib cumulative
return chart without duplicating the mission contract. QuantStats and
pyfolio/empyrical are alternative renderers; neither may replace the contract
evaluation.

Requires: pandas, matplotlib
"""

from __future__ import annotations

import argparse
import base64
import html
import io
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "core"))
import report as contract_report

RETURN_COLUMNS = ("candidate", "momentum", "buy_and_hold")


def returns_frame(artifact: dict[str, Any]) -> pd.DataFrame:
    """Build the dated metrics-store view required by a real tearsheet."""
    rows = artifact.get("daily_returns")
    if not rows:
        raise ValueError(
            "artifact.daily_returns is required for a production tearsheet; "
            "synthetic verdict fixtures intentionally do not contain it"
        )
    frame = pd.DataFrame(rows)
    required = {"date", "regime", *RETURN_COLUMNS}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"daily_returns is missing columns: {', '.join(missing)}")
    frame["date"] = pd.to_datetime(frame["date"], utc=True)
    return frame.sort_values("date").set_index("date")


def drawdown_table(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column in RETURN_COLUMNS:
        wealth = (1 + frame[column]).cumprod()
        drawdown = wealth / wealth.cummax() - 1
        trough = drawdown.idxmin()
        peak = wealth.loc[:trough].idxmax()
        recovered = wealth.loc[trough:][wealth.loc[trough:] >= wealth.loc[peak]]
        rows.append(
            {
                "arm": column,
                "maximum_drawdown": float(drawdown.loc[trough]),
                "peak": peak.date().isoformat(),
                "trough": trough.date().isoformat(),
                "recovery": (
                    recovered.index[0].date().isoformat()
                    if not recovered.empty
                    else "not recovered"
                ),
            }
        )
    return pd.DataFrame(rows).set_index("arm")


def regime_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Annualized diagnostics by named regime, never aggregate-only."""
    grouped = frame.groupby("regime", observed=True)
    rows = []
    for regime, values in grouped:
        row: dict[str, Any] = {"regime": regime, "observations": len(values)}
        for column in RETURN_COLUMNS:
            standard_deviation = values[column].std(ddof=1)
            row[f"{column}_sharpe"] = (
                float(values[column].mean() / standard_deviation * 252**0.5)
                if standard_deviation and not pd.isna(standard_deviation)
                else float("nan")
            )
        rows.append(row)
    return pd.DataFrame(rows).set_index("regime")


def cumulative_chart(frame: pd.DataFrame) -> str:
    wealth = (1 + frame[list(RETURN_COLUMNS)]).cumprod()
    axis = wealth.plot(title="Cumulative net return by declared arm")
    axis.set_ylabel("growth of one unit")
    axis.figure.tight_layout()
    buffer = io.BytesIO()
    axis.figure.savefig(buffer, format="png", dpi=144)
    plt.close(axis.figure)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def render_html(artifact: dict[str, Any]) -> str:
    verdict = contract_report.evaluate(artifact, contract_report.load_mission_text())
    frame = returns_frame(artifact)
    report_text = contract_report.render(verdict)
    regimes = regime_table(frame)
    worst = regimes["candidate_sharpe"].idxmin()
    failures = pd.DataFrame(artifact["failure_cases"])
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>Mission 03 contract tearsheet</title>
<body>
<h1>Mission 03 contract tearsheet</h1>
<pre>{html.escape(report_text)}</pre>
<h2>Cumulative net returns</h2>
<img alt="Cumulative net returns for candidate and both baselines"
     src="data:image/png;base64,{cumulative_chart(frame)}">
<h2>Drawdowns</h2>
{drawdown_table(frame).to_html(float_format=lambda value: f"{value:.4f}")}
<h2>Regimes</h2>
<p>Worst candidate regime: <strong>{html.escape(str(worst))}</strong></p>
{regimes.to_html(float_format=lambda value: f"{value:.4f}")}
<h2>Declared failure cases</h2>
{failures.to_html(index=False)}
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--output", type=Path, default=Path("tearsheet.html"))
    args = parser.parse_args()
    artifact = json.loads(args.artifact.read_text())
    rendered = render_html(artifact)
    args.output.write_text(rendered)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
