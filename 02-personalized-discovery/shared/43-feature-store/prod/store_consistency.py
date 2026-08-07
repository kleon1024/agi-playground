"""Production as-of consistency audit over persisted store reads.

Stage 43's store exists so training and serving read the same frozen
value. This path reads the read envelope the core script emits
(`core/feature_store.py --emit-log /tmp/store-reads.json`) and audits
the two sides the way a serving team would audit a live store: per key,
does the served feature vector match the one the model trained on, and
does the served distribution differ from the training snapshot?

The check answers the case-finding question of the stage: when the
store is bypassed or a read recomputes on the fly, the divergence shows
up as a served value the model never saw. The audit names the keys and
the feature, so the owning team knows where the two reads split.

Requires: pandas

Run:
    python store_consistency.py /tmp/store-reads.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

AGE_TOLERANCE = 1e-6  # a store read must serve the training value exactly


def audit(rows: list[dict[str, object]]) -> tuple[pd.DataFrame, list[str]]:
    """Per-key served-vs-trained comparison and the failing keys."""
    records = []
    for row in rows:
        item_id = str(row["id"])
        store_feats = dict(row["store"])  # type: ignore[arg-type]
        naive_feats = dict(row["naive"])  # type: ignore[arg-type]
        for feature in sorted(set(store_feats) | set(naive_feats)):
            trained = float(store_feats.get(feature, 0.0))
            served = float(naive_feats.get(feature, 0.0))
            records.append(
                {
                    "item": item_id,
                    "feature": feature,
                    "trained": trained,
                    "served": served,
                    "delta": served - trained,
                    "store_score": float(row["store_score"]),
                    "naive_score": float(row["naive_score"]),
                }
            )
    frame = pd.DataFrame(records)
    drifted = frame[frame["delta"].abs() > AGE_TOLERANCE]
    failing = sorted(
        f"{item}/{feature}" for item, feature in zip(drifted["item"], drifted["feature"])
    )
    return frame, failing


def render(frame: pd.DataFrame, failing: list[str]) -> None:
    n_items = frame["item"].nunique()
    print("as-of consistency audit over the emitted store reads:")
    print(f"  keys checked: {len(frame)} rows across {n_items} items")
    per_feature = frame.groupby("feature")["delta"].agg(["mean", "max", "count"])
    for feature, stats in per_feature.iterrows():
        print(
            f"  feature {feature}: mean served-vs-trained delta "
            f"{stats['mean']:+.2f}, max {stats['max']:+.2f} "
            f"({int(stats['count'])} keys)"
        )
    print(f"  keys whose served value differs from training: {len(failing)}")
    for key in failing[:8]:
        print(f"    {key}")
    print()
    if failing:
        print("verdict: DIVERGENT -- the served read recomputed a feature")
        print("the model never trained on. Keys above; the store is bypassed")
        print("on this read path.")
    else:
        print("verdict: CONSISTENT -- every served value matches the training")
        print("snapshot. The store is doing its job.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: store_consistency.py <store-reads.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame, failing = audit(envelope["items"])
    render(frame, failing)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
