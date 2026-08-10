"""Production stale-embedding audit over the emitted query log.

Stage 20 retrieves by embedding similarity. The failure mode this path
exists for is the embedding that goes stale: between embedding runs the
doc vectors drift, and a system that serves the old snapshot does not
know which queries it is silently degrading — the offline/online
consistency gap.

This path reads the envelope the core script emits
(`core/two_tower.py --emit-log /tmp/dense-envelope.json`), compares the
recall@5 each query gets against fresh versus stale doc embeddings, and
stratifies the gap by head and tail — the case-finding that shows where
embedding freshness decisions have to be made.

Requires: pandas

Run:
    python dense_audit.py /tmp/dense-envelope.json
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
                    "fresh": q["fresh"],
                    "stale": q["stale"],
                }
            )
    return pd.DataFrame(rows)


def render(frame: pd.DataFrame) -> None:
    agg = frame["stale"].mean() - frame["fresh"].mean()
    print("stale-embedding audit over the 20-query log:")
    print(f"  aggregate recall@5: fresh {frame['fresh'].mean():.3f} -> "
          f"stale {frame['stale'].mean():.3f} (gap {agg:+.3f})")
    print()
    print("  stratum  queries  fresh  stale   gap")
    for stratum in ("head", "tail"):
        sub = frame[frame["stratum"] == stratum]
        gap = sub["stale"].mean() - sub["fresh"].mean()
        print(
            f"  {stratum:<8} {len(sub):<8} {sub['fresh'].mean():.3f}  "
            f"{sub['stale'].mean():.3f}   {gap:+.3f}"
        )
    head = frame[frame["stratum"] == "head"]
    tail = frame[frame["stratum"] == "tail"]
    head_gap = head["stale"].mean() - head["fresh"].mean()
    tail_gap = tail["stale"].mean() - tail["fresh"].mean()
    print()
    if tail_gap < -0.4 and head_gap > -0.1:
        print("verdict: STALE EMBEDDING DIVERGES IN THE TAIL -- the")
        print(f"fresh-versus-stale gap is {tail_gap:+.3f} on tail queries")
        print(f"against {head_gap:+.3f} on head. Head queries survive a")
        print("stale index; tail queries lose most of their recall. An")
        print("aggregate consistency check reports the mean gap and")
        print("approves the stale snapshot; the stratified view says the")
        print("tail is where embedding freshness has to be decided.")
    else:
        print("verdict: STALE EMBEDDING GAP SPREAD -- head and tail")
        print("degrade alike or neither; no concentration to act on.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: dense_audit.py <dense-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
