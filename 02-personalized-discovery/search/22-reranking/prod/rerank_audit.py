"""Production served-k audit over the emitted query log.

Stage 22 reranks the first stage's top candidates. The failure mode
this path exists for is the eval k that disagrees with the served k: a
reranker is approved offline at NDCG@10 while the page serves three
slots, and gains that land below position 3 never reach a user. On the
tail the reranker's rich features can also misfire at the top — the
offline metric says it helps, the served surface says it hurts.

This path reads the envelope the core script emits
(`core/rerank_top_k.py --emit-log /tmp/rerank-envelope.json`), compares
the @10 and @3 deltas per stratum, and reports where the two surfaces
disagree — the offline/online consistency check for the reranker.

Requires: pandas

Run:
    python rerank_audit.py /tmp/rerank-envelope.json
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
                    "first10": q["first10"],
                    "rerank10": q["rerank10"],
                    "first3": q["first3"],
                    "rerank3": q["rerank3"],
                }
            )
    return pd.DataFrame(rows)


def render(frame: pd.DataFrame) -> None:
    d10 = frame["rerank10"].mean() - frame["first10"].mean()
    d3 = frame["rerank3"].mean() - frame["first3"].mean()
    print("served-k audit over the 20-query log:")
    print(f"  aggregate @10: first {frame['first10'].mean():.3f} -> "
          f"rerank {frame['rerank10'].mean():.3f} (delta {d10:+.3f})")
    print(f"  aggregate @3:  first {frame['first3'].mean():.3f} -> "
          f"rerank {frame['rerank3'].mean():.3f} (delta {d3:+.3f})")
    print()
    print("  stratum  queries  delta@10  delta@3  agree?")
    for stratum in ("head", "tail"):
        sub = frame[frame["stratum"] == stratum]
        s10 = sub["rerank10"].mean() - sub["first10"].mean()
        s3 = sub["rerank3"].mean() - sub["first3"].mean()
        agree = "yes" if (s10 >= 0) == (s3 >= 0) else "NO"
        print(
            f"  {stratum:<8} {len(sub):<8} {s10:+.3f}    {s3:+.3f}    {agree}"
        )
    tail = frame[frame["stratum"] == "tail"]
    t10 = tail["rerank10"].mean() - tail["first10"].mean()
    t3 = tail["rerank3"].mean() - tail["first3"].mean()
    print()
    if t10 > 0 and t3 < 0:
        print("verdict: SERVING-K DIVERGENCE -- the @10 experiment")
        print(f"approves the reranker (aggregate {d10:+.3f}) while the")
        print(f"served @3 report says the page got worse ({d3:+.3f}).")
        print(f"The entire loss is tail ({t3:+.3f} at @3 against {t10:+.3f}")
        print("at @10): the reranker's fixes land in the middle of the")
        print("list, below the three served slots. Report at the served")
        print("k, audit per position, and slice the rerank experiment")
        print("by head and tail before shipping it.")
    else:
        print("verdict: SURFACES AGREE -- the @10 and @3 deltas point")
        print("the same way in every stratum; no served-k divergence.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: rerank_audit.py <rerank-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
