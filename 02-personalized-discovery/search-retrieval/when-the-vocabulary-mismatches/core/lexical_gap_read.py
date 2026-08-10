"""The vocabulary mismatch that cuts the candidate, read.

Stage 11's BM25 index scores exact terms, and the synonym detour showed
partial matches being under-ranked. This chapter is the harder half of
the same failure: a relevant document that shares no query term scores
0.0000 and is cut before ranking — it never enters the candidate set,
so no ranker downstream can recover it. This script measures the cut,
then the fix: synonym expansion that lifts the missed document back
into the set, and the precision cost of the broader query.

Run:
    uv run python core/lexical_gap_read.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
from bm25_retrieval import DOCS, bm25


def main() -> None:
    docs = dict(DOCS)
    docs["doc6"] = "affordable earbuds budget friendly sound"
    docs["doc7"] = "cheap running shoes on sale"

    relevant = {"doc6"}  # the declared relevant doc for "cheap headphones"
    query = "cheap headphones"

    print("vocabulary mismatch, read — the cut before ranking:")
    plain = bm25(query, docs)
    top3_plain = [d for d, _ in plain[:3]]
    rec_plain = 1.0 if any(d in relevant for d in top3_plain) else 0.0
    print(f"  query '{query}' (unexpanded):")
    for doc, score in plain[:5]:
        marker = "  <-- relevant, cut" if doc == "doc6" else ""
        print(f"    {doc:<6} {score:.4f}  {docs[doc]}{marker}")
    print(f"    recall@3 = {rec_plain:.2f}  (doc6 scored {dict(plain)['doc6']:.4f})")

    print("\n  fix: expand 'cheap' with its synonyms 'affordable budget':")
    expanded = "cheap headphones affordable budget"
    ranked = bm25(expanded, docs)
    top3_expanded = [d for d, _ in ranked[:3]]
    rec_expanded = 1.0 if any(d in relevant for d in top3_expanded) else 0.0
    for doc, score in ranked[:5]:
        marker = "  <-- relevant, recovered" if doc == "doc6" else ""
        print(f"    {doc:<6} {score:.4f}  {docs[doc]}{marker}")
    print(f"    recall@3 = {rec_expanded:.2f}")

    print("\n  trade: the broader query also matches 'cheap running shoes'")
    print("  (doc7) — expansion raised the candidate count and pulled in")
    print("  a false positive for headphones. Recall is fixed; precision")
    print("  must be re-checked, which is what reranking is for.")


if __name__ == "__main__":
    main()
