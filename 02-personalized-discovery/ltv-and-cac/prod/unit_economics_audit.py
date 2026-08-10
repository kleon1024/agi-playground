"""Production unit-economics audit over the emitted retention curves.

Stage 55's read shows LTV/CAC deciding which channel the platform can
afford. The failure mode this path exists for is the window that
decides the verdict: LTV/CAC is a curve over the measured horizon, not
a number, and a channel that ramps slowly looks unaffordable at a short
window and dominant at a long one. This path reads the envelope the
core script emits (`core/unit_economics.py --emit-log
/tmp/unit-economics-envelope.json`) and recomputes LTV/CAC per horizon
per channel, the way a growth finance team re-measures unit economics
before scaling an acquisition bet.

The check answers the case-finding question of the stage: before you
declare a channel profitable or dead, check whether the window you
measured would flip the verdict.

Requires: pandas

Run:
    python unit_economics_audit.py /tmp/unit-economics-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def panel(envelope: dict[str, object]) -> pd.DataFrame:
    horizons = [int(h) for h in envelope["horizons"]]  # type: ignore[arg-type]
    rows = []
    for channel in envelope["channels"]:  # type: ignore[union-attr]
        retention = [float(r) for r in channel["retention"]]
        revenue = float(channel["revenue_per_month"])
        cac = float(channel["cac"])
        row = {"channel": channel["name"], "cac": cac}
        for h in horizons:
            row[f"ltv_{h}m"] = sum(retention[:h]) * revenue
        rows.append(row)
    frame = pd.DataFrame(rows)
    for h in horizons:
        frame[f"ratio_{h}m"] = frame[f"ltv_{h}m"] / frame["cac"]
    return frame


def render(frame: pd.DataFrame, horizons: list[int]) -> None:
    short = horizons[1] if len(horizons) > 1 else horizons[0]
    long = horizons[-1]
    print("unit-economics audit (ltv/cac per measured window):")
    print(f"  {'channel':<16} " + " ".join(f"{h:>4}m" for h in horizons))
    for _, row in frame.iterrows():
        ratios = [row[f"ratio_{h}m"] for h in horizons]
        print(f"  {row['channel']:<16} " + " ".join(f"{r:>6.2f}" for r in ratios))
    print()
    short_rank = frame.sort_values(f"ratio_{short}m", ascending=False)
    long_rank = frame.sort_values(f"ratio_{long}m", ascending=False)
    if list(short_rank["channel"]) == list(long_rank["channel"]):
        print("verdict: WINDOW STABLE -- channel ranking is the same at")
        print(f"the {short}m and {long}m windows; the horizon does not")
        print("change the acquisition verdict.")
        return
    flipped = short_rank["channel"].iloc[0]
    true_leader = long_rank["channel"].iloc[0]
    print(f"verdict: WINDOW TRUNCATED -- at {short}m the top channel is")
    print(f"'{flipped}', and at {long}m it is '{true_leader}': the window")
    print("you measured decides which channel you call the acquisition")
    print("bet. Channels that ramp slowly and stay (referral) are")
    print("understated at short windows; channels that decay fast (paid")
    print("installs) rank above them at short windows and never improve.")
    print("Re-measure LTV on the full retention curve, modeled from the")
    print("cohort's own recency-frequency data, before scaling spend.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: unit_economics_audit.py <unit-economics-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    horizons = [int(h) for h in envelope["horizons"]]
    frame = panel(envelope)
    render(frame, horizons)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
