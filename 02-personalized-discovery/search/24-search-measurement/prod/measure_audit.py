"""Production funnel audit over the emitted slice log.

Stage 24 measures the search funnel from logs. The failure mode this
path exists for is the funnel metric that hides a collapsed slice: the
aggregate conversion rate looks normal while one stratum — here the
mobile tail — is failing, and nobody sees it until the slice is
reported.

This path reads the envelope the core script emits
(`core/zero_results.py --emit-log /tmp/measure-envelope.json`), computes
the funnel per slice, compares each slice with the aggregate, and names
the slice that diverges — the case-finding for the funnel report.

Requires: pandas

Run:
    python measure_audit.py /tmp/measure-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def panel(envelope: dict[str, object]) -> pd.DataFrame:
    rows = []
    for s in envelope["slices"]:  # type: ignore[assignment]
        rows.append(
            {
                "slice": s["slice"],
                "queries": s["queries"],
                "zero": s["zero"],
                "click": s["click"],
                "conv": s["conv"],
            }
        )
    frame = pd.DataFrame(rows)
    frame["zero_rate"] = frame["zero"] / frame["queries"]
    frame["ctr"] = frame["click"] / frame["queries"]
    frame["conv_rate"] = frame["conv"] / frame["queries"]
    return frame


def render(frame: pd.DataFrame) -> None:
    q = frame["queries"].sum()
    agg_conv = frame["conv"].sum() / q
    agg_zero = frame["zero"].sum() / q
    print("funnel audit over the four slices:")
    print(f"  aggregate: {q:,} queries, zero {agg_zero:.1%}, "
          f"conversion {agg_conv:.2%}")
    print()
    print("  slice          queries  zero    click   conversion")
    for _, row in frame.iterrows():
        print(
            f"  {row['slice']:<14} {int(row['queries']):>6,}  "
            f"{row['zero_rate']:.0%}   {row['ctr']:.0%}   "
            f"{row['conv_rate']:.2%}"
        )
    worst = frame.loc[frame["conv_rate"].idxmin()]
    print()
    if worst["conv_rate"] < agg_conv / 3:
        print("verdict: HIDDEN SLICE -- the aggregate funnel")
        print(f"({agg_conv:.2%} conversion, {agg_zero:.1%} zero) looks")
        print(f"normal while {worst['slice']} converts at "
              f"{worst['conv_rate']:.2%} with a {worst['zero_rate']:.0%}")
        print("zero-result rate. The slice is a fraction of traffic, so")
        print("it barely moves the aggregate — report the funnel per")
        print("slice, and treat a slice whose rate is a third of the")
        print("aggregate as an incident, not a rounding error.")
    else:
        print("verdict: SLICES CONSISTENT -- no slice diverges from the")
        print("aggregate by more than a factor of three.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: measure_audit.py <measure-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
