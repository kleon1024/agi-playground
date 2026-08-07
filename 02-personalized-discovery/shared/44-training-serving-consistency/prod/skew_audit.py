"""Production distribution audit over logged versus live features.

Stage 44's skew is a pipeline property: the training set holds the
feature vector that was logged at decision time, while serving reads
the live vector. This path reads the envelope the core script emits
(`core/skew.py --emit-log /tmp/skew-envelope.json`) and runs the
distribution check a platform would run between its training and
serving environments: per feature, how far has the live distribution
drifted from the logged one, and which items moved.

The check answers the case-finding question of the stage. It is the
same comparison TensorFlow Data Validation encodes in its skew
detector: the training environment and the serving environment must
match per feature, or the offline ranking is honest about a world that
no longer exists (Baylor et al., TFX, KDD 2017; Breck et al., Data
Validation for Machine Learning, SysML 2019).

Requires: pandas

Run:
    python skew_audit.py /tmp/skew-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

TOLERANCE = 1e-6


def audit(
    logged: list[dict[str, object]], live: list[dict[str, object]]
) -> tuple[pd.DataFrame, list[str]]:
    """Per-item logged-vs-live deltas and the features that diverged."""
    logged_frame = pd.DataFrame(logged).set_index("id")
    live_frame = pd.DataFrame(live).set_index("id")
    features = [c for c in logged_frame.columns if c not in ("id",)]
    records = []
    for item_id in logged_frame.index:
        for feature in features:
            trained = float(logged_frame.loc[item_id, feature])
            served = float(live_frame.loc[item_id, feature])
            records.append(
                {
                    "item": item_id,
                    "feature": feature,
                    "logged": trained,
                    "live": served,
                    "delta": served - trained,
                }
            )
    frame = pd.DataFrame(records)
    drifted = frame[frame["delta"].abs() > TOLERANCE]
    failing = sorted(drifted["feature"].unique())
    return frame, failing


def render(frame: pd.DataFrame, failing: list[str]) -> None:
    n_items = frame["item"].nunique()
    print("logged-vs-live distribution audit over the emitted vectors:")
    print(f"  items compared: {n_items}")
    frame["abs_delta"] = frame["delta"].abs()
    per_feature = frame.groupby("feature")["abs_delta"].agg(["mean", "max", "count"])
    for feature, stats in per_feature.iterrows():
        print(
            f"  feature {feature}: mean |live-logged| "
            f"{stats['mean']:.3f}, max {stats['max']:.3f} "
            f"({int(stats['count'])} items)"
        )
    print(f"  features whose live distribution differs from logged: {len(failing)}")
    for feature in failing:
        print(f"    {feature}")
    print()
    if failing:
        print("verdict: DIVERGENT -- the live feature distribution no longer")
        print("matches the logged one the model trained on. Features above;")
        print("the offline ranking is honest about a world that ended.")
    else:
        print("verdict: CONSISTENT -- live features match the logged training")
        print("distribution per item. The training set still describes serving.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: skew_audit.py <skew-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame, failing = audit(envelope["logged"], envelope["live"])
    render(frame, failing)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
