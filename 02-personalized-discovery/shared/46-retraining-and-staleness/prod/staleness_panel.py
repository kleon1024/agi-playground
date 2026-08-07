"""Production staleness panel: rank error per cohort against snapshot age.

Stage 46's staleness grows with snapshot age, but not uniformly: cohorts
whose rates move fast degrade in hours while slow cohorts stay useful
for days. This path reads the item table the core script emits
(`core/staleness.py --emit-log /tmp/staleness-envelope.json`) and builds
the panel a team would use to decide the retraining trigger: per cohort,
how many pairwise orderings does a snapshot from hour 0 get wrong at
each later hour, and does the volatile cohort out-degrade the stable
one?

The check answers the case-finding question of the stage: a retraining
cadence tuned to the aggregate average leaves the volatile cohort stale
longest, because the average is dominated by the slow movers.

Requires: pandas

Run:
    python staleness_panel.py /tmp/staleness-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def ctr_at(row: pd.Series, hour: int) -> float:
    return float(row["base"]) + float(row["trend"]) * hour


def wrong_pairs(items: pd.DataFrame, model_hour: int, truth_hour: int) -> int:
    """Pairwise orderings the snapshot model gets wrong within the frame."""
    model_order = items.sort_values(
        "base", key=lambda s: [ctr_at(row, model_hour) for _, row in items.iterrows()],
        ascending=False,
    )["id"].tolist()
    truth_order = items.sort_values(
        "base", key=lambda s: [ctr_at(row, truth_hour) for _, row in items.iterrows()],
        ascending=False,
    )["id"].tolist()
    model_pos = {item_id: p for p, item_id in enumerate(model_order)}
    truth_pos = {item_id: p for p, item_id in enumerate(truth_order)}
    ids = items["id"].tolist()
    errors = 0
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            id_a, id_b = ids[a], ids[b]
            if (model_pos[id_a] < model_pos[id_b]) != (truth_pos[id_a] < truth_pos[id_b]):
                errors += 1
    return errors


def panel(items: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cohort in ["all", "volatile", "stable"]:
        frame = items if cohort == "all" else items[items["cohort"] == cohort]
        rows.append(
            {
                "cohort": cohort,
                "items": len(frame),
                "snap0_at_6": wrong_pairs(frame, 0, 6),
                "snap0_at_12": wrong_pairs(frame, 0, 12),
                "snap6_at_12": wrong_pairs(frame, 6, 12),
            }
        )
    return pd.DataFrame(rows)


def render(frame: pd.DataFrame) -> None:
    print("staleness panel, rank error vs snapshot age per cohort:")
    print(f"  {'cohort':<9} {'items':>5}  {'snap0@6':>7}  {'snap0@12':>8}  {'snap6@12':>8}")
    for _, row in frame.iterrows():
        print(
            f"  {row['cohort']:<9} {int(row['items']):>5}  "
            f"{int(row['snap0_at_6']):>7}  {int(row['snap0_at_12']):>8}  "
            f"{int(row['snap6_at_12']):>8}"
        )
    volatile = frame[frame["cohort"] == "volatile"].iloc[0]
    stable = frame[frame["cohort"] == "stable"].iloc[0]
    print()
    if int(volatile["snap0_at_6"]) > int(stable["snap0_at_6"]):
        print("verdict: VOLATILE FIRST -- the volatile cohort out-degrades the")
        print("stable one by hour 6, so a retraining trigger tuned to the")
        print("aggregate average leaves the fast movers stale longest. The")
        print("trigger should follow the measured error per cohort, not a")
        print("calendar or the average.")
    else:
        print("verdict: UNIFORM -- cohorts degrade at the same rate; a single")
        print("aggregate trigger is enough.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: staleness_panel.py <staleness-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    items = pd.DataFrame(envelope["items"])
    frame = panel(items)
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
