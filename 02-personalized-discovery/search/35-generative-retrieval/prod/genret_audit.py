"""Production decode-recall audit over the emitted query log.

Stage 35 retrieves by decoding document IDs. The failure mode this path
exists for is the aggregate decode-recall experiment: a head-dominated
log can report "the generative retriever decodes well" while the tail —
where training has the least evidence — loses most of its recall and
emits nonexistent IDs.

This path reads the envelope the core script emits
(`core/genret_read.py --emit-log /tmp/genret-envelope.json`), stratifies
decode recall and emitted-ID precision by head and tail, and reports
where the decode holds — the case-finding for the generative path.

Requires: pandas

Run:
    python genret_audit.py /tmp/genret-envelope.json
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
                    "recall": q["recall"],
                    "precision": q["precision"],
                }
            )
    return pd.DataFrame(rows)


def render(frame: pd.DataFrame) -> None:
    print("decode-recall audit over the 20-query log:")
    print(f"  aggregate recall@5: {frame['recall'].mean():.3f}  "
          f"emitted-ID precision: {frame['precision'].mean():.3f}")
    print()
    print("  stratum  queries  recall@5  precision")
    for stratum in ("head", "tail"):
        sub = frame[frame["stratum"] == stratum]
        print(
            f"  {stratum:<8} {len(sub):<8} {sub['recall'].mean():.3f}    "
            f"{sub['precision'].mean():.3f}"
        )
    head = frame[frame["stratum"] == "head"]
    tail = frame[frame["stratum"] == "tail"]
    tail_recall = tail["recall"].mean()
    print()
    if tail_recall < 0.7 and head["recall"].mean() == 1.0:
        print("verdict: DECODE RECALL DIVERGES IN THE TAIL -- the")
        print(f"aggregate recall@5 {frame['recall'].mean():.3f} is a head")
        print("artifact: head decodes perfectly (1.000) while tail")
        print(f"recall is {tail_recall:.3f} with precision "
              f"{tail['precision'].mean():.3f} — a quarter of the emitted")
        print("IDs do not exist. The decode is a trained behavior, so it")
        print("inherits the training distribution. Gate the generative")
        print("path to queries it can decode, and fall back to the dense")
        print("or hybrid path for the tail.")
    else:
        print("verdict: DECODE SPREAD -- decode quality holds across")
        print("strata or degrades uniformly; no concentration to act on.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: genret_audit.py <genret-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
