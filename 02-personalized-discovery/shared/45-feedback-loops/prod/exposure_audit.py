"""Production exposure-concentration audit over the served log.

Stage 45's loop entrenches what it shows: exposure concentrates on the
head until the tail's true rate is unmeasurable. This path reads the
per-item ledger the core script emits (`core/popularity_collapse.py
--emit-log /tmp/loop-envelope.json`) and audits it the way a team audits
its own serving log: per band of the catalogue, what share of
impressions did each band get, what CTR did the log measure, and can the
log prove anything about the bands it stopped showing?

The check answers the case-finding question of the stage: the log cannot
prove the tail is worse, because the tail was never shown. The audit
names the concentration and the measurement gap per band, which is what
decides whether exploration is a feature or a correction.

Requires: pandas

Run:
    python exposure_audit.py /tmp/loop-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def audit(items: list[dict[str, object]]) -> pd.DataFrame:
    """Band the catalogue by true CTR and aggregate the exposure ledger."""
    frame = pd.DataFrame(items)
    frame = frame.sort_values("true_ctr", ascending=False).reset_index(drop=True)
    n = len(frame)
    head = round(n * 0.25)
    tail = round(n * 0.25)
    frame["band"] = ["head"] * head + ["mid"] * (n - head - tail) + ["tail"] * tail
    rows = []
    for band in ("head", "mid", "tail"):
        group = frame[frame["band"] == band]
        impressions = int(group["shown"].sum())
        clicks = int(group["clicks"].sum())
        rows.append(
            {
                "band": band,
                "items": len(group),
                "impressions": impressions,
                "impression_share": impressions / int(frame["shown"].sum()),
                "measured_ctr": clicks / impressions if impressions else 0.0,
                "true_ctr": float(group["true_ctr"].mean()),
                "items_never_shown": int((group["shown"] == 0).sum()),
            }
        )
    return pd.DataFrame(rows)


def render(frame: pd.DataFrame) -> None:
    print("exposure-concentration audit over the served log:")
    total = int(frame["impressions"].sum())
    print(f"  total impressions: {total}")
    for _, row in frame.iterrows():
        print(
            f"  {row['band']:<5} {int(row['items']):>2} items: "
            f"{int(row['impressions']):>4} impressions ({row['impression_share']:.0%}), "
            f"measured ctr {row['measured_ctr']:.4f}, true ctr {row['true_ctr']:.4f}, "
            f"never shown {int(row['items_never_shown'])}"
        )
    head = frame[frame["band"] == "head"].iloc[0]
    tail = frame[frame["band"] == "tail"].iloc[0]
    print()
    if head["impression_share"] >= 0.8 and tail["impressions"] < 30:
        print("verdict: CONCENTRATED -- the head holds nearly all exposure and")
        print(f"the tail's CTR is measured on {int(tail['impressions'])} impressions")
        print("(0.0000), so the log cannot prove the tail is worse; it only")
        print("proves the tail was not shown.")
        print(f"  head impression share: {head['impression_share']:.0%};")
        print(f"  tail impression share: {tail['impression_share']:.0%},")
        print(f"  tail true ctr {tail['true_ctr']:.4f} vs measured "
              f"{tail['measured_ctr']:.4f}.")
    else:
        print("verdict: BALANCED -- every band kept enough exposure to be")
        print("measured. The log can still describe the tail.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: exposure_audit.py <loop-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = audit(envelope["items"])
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
