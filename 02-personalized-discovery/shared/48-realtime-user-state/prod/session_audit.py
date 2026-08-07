"""Production session-lift audit over the emitted cohort rows.

Stage 48's read shows the session re-ranking a slate. The failure mode
this path exists for is the lift that is real in the aggregate and
uneven underneath: the realtime boost pays, but the payment grows with
session depth, and the shallow sessions that own the most traffic get a
signal close to a coin flip. This path reads the envelope the core
script emits (`core/session_state.py --emit-log
/tmp/session-envelope.json`) and stratifies the lift by depth and by
traffic share, the way a serving team sizes realtime feature spend from
logged sessions instead of from the blended average.

The check answers the case-finding question of the stage: before you
put another realtime feature on the request path, find out which
sessions actually pay for it.

Requires: pandas

Run:
    python session_audit.py /tmp/session-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def panel(envelope: dict[str, object]) -> pd.DataFrame:
    rows = pd.DataFrame(envelope["cohorts"])  # type: ignore[arg-type]
    rows["lift"] = rows["realtime_ctr"] - rows["batch_ctr"]
    rows["weighted_lift"] = rows["lift"] * rows["traffic"]
    return rows


def render(frame: pd.DataFrame) -> None:
    print("session-lift audit (served CTR by session depth):")
    print(f"  {'depth':>5} {'signal q':>8} {'traffic':>8}  {'batch':>6} "
          f"{'realtime':>9} {'lift':>7} {'share of lift':>14}")
    total_lift = float(frame["weighted_lift"].sum())
    for _, row in frame.iterrows():
        share = row["weighted_lift"] / total_lift if total_lift else 0.0
        print(
            f"  {int(row['depth']):>5} {row['q']:>8.2f} "
            f"{row['traffic']:>8.0%}  {row['batch_ctr']:.4f} "
            f"{row['realtime_ctr']:.4f} {row['lift']:+.4f} "
            f"{share:>13.0%}"
        )
    weighted = frame["weighted_lift"].sum()
    deep = frame[frame["depth"] == 4].iloc[0]
    shallow = frame[frame["depth"] == 1].iloc[0]
    print()
    print(f"traffic-weighted lift: {weighted:+.4f}; "
          f"deep-session (depth 4) lift: {deep['lift']:+.4f}; "
          f"single-dwell (depth 1) lift: {shallow['lift']:+.4f}")
    ratio = abs(float(shallow["lift"])) / abs(float(deep["lift"]))
    if ratio >= 0.65:
        print("verdict: EVEN LIFT -- the single-dwell sessions earn at least")
        print("65% of the deep-session lift per session; the realtime spend")
        print("pays roughly the same across the depth distribution.")
    else:
        print("verdict: SHALLOW SESSION -- the single-dwell sessions that own")
        print(f"70% of traffic earn {ratio:.0%} of the deep-session lift per")
        print("session. The blended lift is what the cost model sees, but the")
        print("realtime cost is paid per request for every session, so deep")
        print("sessions earn the better ROI. Stratify by depth before sizing")
        print("the realtime feature spend, and gate the boost on a second")
        print("signal for depth-1 sessions.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: session_audit.py <session-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
