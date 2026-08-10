"""The conversational surface, read from the recorded search runs.

The chapter's question: when the result page becomes a conversation, what
does the loop actually change? This script reads two committed records --
the AOL query-log session-recovery read and the conversational-search
resolution audit -- and prints the per-query-versus-session verdict, the
recovery split by stratum, and the correction channel, which is the
evidence the chapter's argument stands on.

Input (recorded, unchanged):
  search/24-search-measurement/when-the-click-is-a-query/runs/
      2026-08-08-query-log-session-recovery.md
  search/36-conversational-search/runs/2026-08-07-session-audit.md

Run:
    uv run python core/conversational_surface.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]

SESSION_READ = (
    ROOT
    / "02-personalized-discovery/search-measurement/"
    "when-the-click-is-a-query/runs/2026-08-08-query-log-session-recovery.md"
)
RESOLUTION_READ = (
    ROOT
    / "02-personalized-discovery/conversational-search/"
    "runs/2026-08-07-session-audit.md"
)


def grab(pattern: str, text: str, label: str, flags: int = 0) -> str:
    m = re.search(pattern, text, flags)
    if not m:
        raise ValueError(f"recorded run no longer contains: {label}")
    return m.group(1)


def main() -> None:
    session = SESSION_READ.read_text()
    resolution = RESOLUTION_READ.read_text()

    per_query_fail = grab(r"per-query report counts ([\d.]+%)", session, "per-query failure share")
    recovered_share = grab(
        r"the session read reclassifies ([\d.]+%)", session, "recovered share"
    )
    # distribution table columns: stratum / queries / traffic / zero-click /
    # recovered / reformulated-no-click / abandoned -- split on whitespace
    # because the recorded table pads columns with varying spaces.
    strata = {}
    for line in session.splitlines():
        cols = line.split()
        if len(cols) == 7 and cols[0] in ("head", "body", "tail"):
            name = cols[0]
            strata[name] = (
                cols[4].rstrip("%"),
                cols[5].rstrip("%"),
                cols[6].rstrip("%"),
            )
    if len(strata) != 3:
        raise ValueError("recorded run no longer contains the head/body/tail strata rows")
    typo = grab(r"near-edit typo fix[^:]*:\s+[\d,]+\s*\(\s*([\d.]+%)", session, "typo channel")
    semantic = grab(
        r"recovered via semantic reformulation:\s+[\d,]+\s*\(\s*([\d.]+%)",
        session,
        "semantic channel",
    )
    agg = grab(r"aggregate resolution:\s*([\d.]+)", resolution, "aggregate resolution")
    head_res = grab(
        r"^\s*head\s+\d+\s+[\d.]+\s+([\d.]+)",
        resolution,
        "head resolution",
        re.MULTILINE,
    )
    tail_res = grab(
        r"^\s*tail\s+\d+\s+[\d.]+\s+([\d.]+)",
        resolution,
        "tail resolution",
        re.MULTILINE,
    )

    print("the conversational surface, read from the recorded search runs:\n")
    print(f"per-query verdict counts {per_query_fail} of queries as failures;")
    print(f"the session read reclassifies {recovered_share} of those as recovered\n")
    print(f"{'stratum':<7}{'recovered':>11}{'reformulated':>15}{'abandoned':>12}")
    for name, (rec, ref, abd) in strata.items():
        print(f"{name:<7}{rec:>10}{ref:>14}{abd:>11}")
    print(f"\ncorrection channel: {typo} near-edit typo fix, {semantic} semantic reformulation")
    print(f"\nsession resolution: aggregate {agg} is a short-session artifact --")
    print(f"head {head_res} vs tail {tail_res} on the recorded audit")
    print("\nreading: the unit of measurement is the session, not the query.")
    print("Recovery concentrates in the tail, and the tail is exactly where")
    print("resolution is hardest -- the conversational surface's addressable")
    print("gap is the reformulated-but-unresolved share, not the click rate.")


if __name__ == "__main__":
    main()
