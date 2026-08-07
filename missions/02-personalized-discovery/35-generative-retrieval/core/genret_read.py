"""Generative retrieval, read: the model emits document IDs directly.

Stage 35 is the frontier of retrieval: instead of scoring a candidate
set, a sequence model generates the document IDs most likely to answer
the query — retrieval without an index scan. This script reads a beam
search over a small ID space.

Run:
    uv run python core/genret_read.py
"""

from __future__ import annotations


def main() -> None:
    # (doc id, generative score)
    ids = [("doc_17", 0.9), ("doc_03", 0.7), ("doc_42", 0.4), ("doc_09", 0.2)]
    print("generative retrieval, read (beam over doc IDs):")
    for doc_id, score in sorted(ids, key=lambda x: -x[1]):
        print(f"  {doc_id}: {score:.1f}")
    top2 = [d for d, _ in sorted(ids, key=lambda x: -x[1])[:2]]
    print(f"  beam top-2: {top2}")
    print("\nreading: the model emits the doc IDs directly, so there is no")
    print("index scan and no candidate generation step. The frontier cost")
    print("is decode latency and the risk of emitting IDs that do not")
    print("exist — the hallucination detour prices that.")


if __name__ == "__main__":
    main()
