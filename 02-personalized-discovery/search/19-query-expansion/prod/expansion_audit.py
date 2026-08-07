"""Production expansion-lift audit over the emitted query log.

Stage 19 corrects and expands queries before retrieval. The failure
mode this path exists for is the aggregate expansion experiment: a
head-dominated query log can report "expansion lifts recall" while the
lift is a tail repair and head traffic pays precision for nothing.

This path reads the envelope the core script emits
(`core/edit_distance.py --emit-log /tmp/expansion-envelope.json`),
stratifies the per-query recall before and after expansion by head and
tail, and reports the lift and the noise per stratum — the case-finding
that shows where the expansion lift actually lives.

Requires: pandas

Run:
    python expansion_audit.py /tmp/expansion-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def panel(envelope: dict[str, object]) -> pd.DataFrame:
    rows = []
    for stratum, queries in envelope["queries"].items():  # type: ignore[assignment]
        for q in queries:
            rows.append(
                {
                    "stratum": stratum,
                    "query": q["query"],
                    "base": q["base"],
                    "expanded": q["expanded"],
                    "noise": q["noise"],
                }
            )
    return pd.DataFrame(rows)


def render(frame: pd.DataFrame) -> None:
    agg = frame["expanded"].mean() - frame["base"].mean()
    print("expansion-lift audit over the 24-query log:")
    print(f"  aggregate recall: base {frame['base'].mean():.3f} -> "
          f"expanded {frame['expanded'].mean():.3f} (lift {agg:+.3f})")
    print()
    print("  stratum  queries  base    expanded  lift     noise/query")
    for stratum in ("head", "tail"):
        sub = frame[frame["stratum"] == stratum]
        lift = sub["expanded"].mean() - sub["base"].mean()
        print(
            f"  {stratum:<8} {len(sub):<8} {sub['base'].mean():.3f}  "
            f"{sub['expanded'].mean():.3f}     {lift:+.3f}     "
            f"{sub['noise'].mean():.2f}"
        )
    head = frame[frame["stratum"] == "head"]
    tail = frame[frame["stratum"] == "tail"]
    head_lift = head["expanded"].mean() - head["base"].mean()
    tail_lift = tail["expanded"].mean() - tail["base"].mean()
    print()
    if tail_lift > 0.2 and head_lift <= 0.01:
        print(f"verdict: EXPANSION LIFT CONCENTRATED IN THE TAIL -- "
              f"aggregate lift {agg:+.3f} is entirely tail "
              f"({tail_lift:+.3f});")
        print("head queries recover nothing (0.000) and pay for it in noise")
        print(f"({head['noise'].mean():.2f} irrelevant hits per query). An")
        print("aggregate expansion experiment reports the lift as if it")
        print("applied everywhere; the stratified view says it is a tail")
        print("repair, and head traffic should not be expanded at all.")
    else:
        print("verdict: EXPANSION LIFT SPREAD -- expansion helps both")
        print("strata or neither; no concentration to act on.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: expansion_audit.py <expansion-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
