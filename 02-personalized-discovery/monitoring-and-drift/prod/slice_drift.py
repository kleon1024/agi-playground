"""Production slice-aware drift panel over the emitted trace.

Stage 47's gap panel catches a break that moves the aggregate. The
failure mode this path exists for is the break that does not: when the
defect is confined to a small traffic segment, the diluted aggregate
stays under threshold while the slice collapses. This path reads the
envelope the core script emits (`core/drift.py --emit-log
/tmp/drift-envelope.json`) and runs the same EWMA gap check per slice,
the way a monitoring team drills into a flat aggregate.

The check answers the case-finding question of the stage: an aggregate
that stays flat is not proof that the page is fine — it is a promise to
slice. The panel names the slice that crossed the threshold while the
aggregate did not.

Requires: pandas

Run:
    python slice_drift.py /tmp/drift-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def ewma_alert_hours(
    observed: list[float], predicted: float, threshold: float
) -> tuple[list[float], int]:
    """EWMA of the prediction-observation gap and the first alert hour."""
    gap_ewma = 0.0
    alert_streak = 0
    first_alert: int | None = None
    series: list[float] = []
    for value in observed:
        gap = predicted - value
        gap_ewma = 0.7 * gap_ewma + 0.3 * gap
        series.append(gap_ewma)
        if gap_ewma > threshold:
            alert_streak += 1
            if alert_streak >= 3 and first_alert is None:
                first_alert = len(series) - 1
        else:
            alert_streak = 0
    return series, -1 if first_alert is None else first_alert


def panel(envelope: dict[str, object]) -> pd.DataFrame:
    predicted = float(envelope["predicted"])
    threshold = float(envelope["threshold"])
    rows = []
    slices: dict[str, dict[str, object]] = envelope["slices"]  # type: ignore[assignment]
    for name in ("aggregate", *slices.keys()):
        if name == "aggregate":
            observed = [float(v) for v in envelope["diluted"]]  # type: ignore[arg-type]
            share = 1.0
        else:
            observed = [float(v) for v in slices[name]["observed"]]  # type: ignore[arg-type]
            share = float(slices[name]["share"])
        _, first_alert = ewma_alert_hours(observed, predicted, threshold)
        rows.append(
            {
                "slice": name,
                "share": share,
                "first": observed[0],
                "last": observed[-1],
                "final_gap": predicted - observed[-1],
                "first_alert": first_alert,
            }
        )
    return pd.DataFrame(rows)


def render(frame: pd.DataFrame, envelope: dict[str, object]) -> None:
    predicted = float(envelope["predicted"])
    threshold = float(envelope["threshold"])
    print(
        f"slice-aware drift panel (predicted {predicted:.3f}, "
        f"threshold {threshold:.3f}):"
    )
    print(f"  {'slice':<12} {'share':>5}  {'observed':>14}  {'gap':>5}  alert")
    for _, row in frame.iterrows():
        share = f"{row['share']:.0%}" if row["share"] < 1.0 else "diluted"
        alert = "never" if row["first_alert"] < 0 else f"hour {int(row['first_alert'])}"
        print(
            f"  {row['slice']:<12} {share:>7}  "
            f"{row['first']:.3f} -> {row['last']:.3f}  "
            f"{row['final_gap']:.3f}  {alert}"
        )
    agg = frame[frame["slice"] == "aggregate"].iloc[0]
    slices = frame[frame["slice"] != "aggregate"]
    hiding = slices[slices["first_alert"] >= 0]
    print()
    if int(agg["first_alert"]) < 0 and len(hiding) > 0:
        names = ", ".join(hiding["slice"].tolist())
        print("verdict: HIDDEN SLICE -- the aggregate stayed under threshold")
        print(f"while {names} crossed it. The break is confined to a small")
        print("traffic segment; the page-level panel cannot see it. Slice-")
        print("aware thresholds per segment are the fix, not a tighter")
        print("aggregate threshold.")
    elif int(agg["first_alert"]) >= 0:
        print("verdict: AGGREGATE FIRST -- the page-level panel caught the")
        print("break before or with the slices. The threshold is doing its job.")
    else:
        print("verdict: QUIET -- no slice crossed the threshold. The panel")
        print("needs finer slicing or a different detector.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: slice_drift.py <drift-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame, envelope)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
