"""The synonym that lexical retrieval cannot see.

BM25 scores exact terms, so a document about 'running footwear' is
invisible to the query 'running shoes'. This script extends the stage's
corpus with a synonym document and shows the zero-score gap — the exact
failure dense retrieval is built to close.

Run:
    uv run python core/synonym_read.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
from bm25_retrieval import DOCS, bm25


def main() -> None:
    syn_docs = dict(DOCS)
    syn_docs["doc6"] = "running footwear lightweight athletic sneakers"
    q = "running shoes"
    print("synonym mismatch, read:")
    print(f"  query: '{q}'")
    for doc, score in bm25(q, syn_docs):
        print(f"  {doc:<6} {score:.4f}  {syn_docs[doc]}")
    print("\nreading: doc6 is semantically on-topic ('running footwear' == ")
    print("running shoes) but only partially matches — 'running' hits, ")
    print("'footwear' does not equal 'shoes' — so it is under-ranked (1.04")
    print("vs doc3's 2.86) even though meaning is nearly identical. Dense")
    print("retrieval matches meaning, which is the gap hybrid search closes")
    print("by running both and fusing.")


if __name__ == "__main__":
    main()
