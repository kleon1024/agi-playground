"""Production lexical recall audit over the emitted BM25 rankings.

Stage 11's BM25 index scores exact terms, and per-query rankings look
fine until you ask whether the right document is even in the candidate
set. The failure mode this path exists for is the vocabulary mismatch
that recall makes visible: a relevant document that shares no query term
scores 0.0000 and is cut before ranking, so no ranker downstream can
surface it.

This path reads the envelope the core script emits
(`core/bm25_retrieval.py --emit-log /tmp/bm25-envelope.json`), measures
recall@3 against the declared relevant documents per query, and reports
the zero-score misses the aggregate hides.

Requires: pandas

Run:
    python bm25_audit.py /tmp/bm25-envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def panel(envelope: dict[str, object]) -> pd.DataFrame:
    rows = []
    for q in envelope["queries"]:  # type: ignore[union-attr]
        relevant = list(q["relevant"])
        ranking = {d: s for d, s in q["ranking"]}
        top3 = [d for d, _ in q["ranking"][:3]]
        hits = [d for d in relevant if d in top3]
        zero = [d for d in relevant if ranking[d] == 0.0]
        rows.append(
            {
                "query": q["query"],
                "freq": q["freq"],
                "relevant": relevant,
                "recall_at_3": len(hits) / len(relevant),
                "mean_overlap": sum(q["overlap"][d] for d in relevant) / len(relevant),
                "zero_score_miss": zero,
            }
        )
    return pd.DataFrame(rows)


def render(frame: pd.DataFrame) -> None:
    print("lexical recall audit over the emitted rankings:")
    print("  query                  freq   recall@3  mean overlap  zero-score misses")
    for _, row in frame.iterrows():
        zero = ", ".join(row["zero_score_miss"]) if row["zero_score_miss"] else "-"
        print(
            f"  {row['query']:<22} {row['freq']:<6} "
            f"{row['recall_at_3']:.2f}      "
            f"{row['mean_overlap']:.2f}          {zero}"
        )
    agg_recall = frame["recall_at_3"].mean()
    gapped = frame[frame["zero_score_miss"].apply(len) > 0]
    print(f"\n  aggregate recall@3 across {len(frame)} queries: {agg_recall:.2f}")
    print()
    if len(gapped) > 0:
        names = ", ".join(gapped["query"].tolist())
        freqs = ", ".join(gapped["freq"].tolist())
        print(f"verdict: LEXICAL GAP -- {len(gapped)} of {len(frame)} queries")
        print(f"lost a relevant document that scored 0.0000 ({names}).")
        print(f"The misses are {freqs} queries, and the aggregate recall")
        print(f"of {agg_recall:.2f} hides them. A document that shares no")
        print("query term never enters the candidate set, so the ranker")
        print("downstream cannot recover it. The fix is synonym-aware")
        print("query expansion, a dense path, or hybrid fusion that")
        print("carries both candidate sources (stages 19-21).")
    else:
        print("verdict: QUIET -- every declared relevant document entered")
        print("the top-3. The lexical index is serving the audited set.")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: bm25_audit.py <bm25-envelope.json>")
        return 2
    envelope = json.loads(Path(argv[0]).read_text())
    frame = panel(envelope)
    render(frame)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
