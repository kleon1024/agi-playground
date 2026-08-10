"""Production new-user cohort audit over the emitted path rows.

Stage 51's read shows the first page improving as the trail builds. The
failure mode this path exists for is the first-page policy that is
healthy in the aggregate and broken underneath: new users arrive by
different onboarding paths, and the aggregate first-page number blends
them, so a path that actively loses users is invisible until you
stratify by path. This path reads the envelope the core script emits
(`core/cold_start.py --emit-log /tmp/cold-start-envelope.json`) and
compares each path against the popularity default and the no-ask
baseline, the way a growth team reads acquisition funnels.

The check answers the case-finding question of the stage: before you
declare the first-page policy healthy, find the path that underperforms
doing nothing.

Requires: pandas

Run:
    python cold_start_audit.py /tmp/cold-start-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def panel(envelope: dict[str, object]) -> pd.DataFrame:
    frame = pd.DataFrame(envelope["paths"])  # type: ignore[arg-type]
    baseline = float(envelope["popularity_baseline_ndcg"])
    frame["vs_baseline"] = frame["first_page_ndcg"] - baseline
    no_ask = frame[frame["path"] == "no-ask"].iloc[0]
    frame["retention_vs_noask"] = frame["retention"] - float(no_ask["retention"])
    return frame


def render(frame: pd.DataFrame) -> None:
    print("new-user cohort audit (first page by onboarding path):")
    print(f"  {'path':<12} {'traffic':>8} {'first-page ndcg':>15} "
          f"{'vs 0.122':>9} {'retention':>9} {'vs no-ask':>9}")
    for _, row in frame.iterrows():
        print(
            f"  {row['path']:<12} {row['traffic']:>8.0%} "
            f"{row['first_page_ndcg']:>15.3f} {row['vs_baseline']:>+9.3f} "
            f"{row['retention']:>9.2f} {row['retention_vs_noask']:>+9.2f}"
        )
    agg_ndcg = (frame["traffic"] * frame["first_page_ndcg"]).sum()
    agg_retention = (frame["traffic"] * frame["retention"]).sum()
    print(f"  {'aggregate':<12} {1.0:>8.0%} {agg_ndcg:>15.3f} "
          f"{agg_ndcg - 0.122:>+9.3f} {agg_retention:>9.2f} "
          f"{agg_retention - 0.20:>+9.2f}")
    below = frame[frame["vs_baseline"] < 0]
    print()
    if len(below) == 0:
        print("verdict: COVERED -- every onboarding path clears the popularity")
        print("baseline on the first page; the cold-start policy is holding.")
        return
    worst = below.sort_values("vs_baseline").iloc[0]
    if float(worst["retention_vs_noask"]) < 0:
        print(f"verdict: NEW-USER GAP -- the {worst['path']} path serves")
        print(f"{float(worst['first_page_ndcg']):.3f} first-page relevance, below")
        print("the 0.122 popularity default, and its retention")
        print(f"({float(worst['retention']):.2f}) is below the no-ask baseline")
        print("(0.20): a confident wrong prior is worse than asking nothing.")
        print("The aggregate (0.254) hides it because 60% of new users arrive")
        print("via popularity; stratify by path before declaring the first-")
        print("page policy healthy, and route the failing path back to the")
        print("default while the prior is re-measured.")
    else:
        print(f"verdict: BELOW BASELINE -- the {worst['path']} path scores below")
        print("the popularity default on first-page relevance but does not")
        print("lose retention; fix the path's relevance, not its traffic.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: cold_start_audit.py <cold-start-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
