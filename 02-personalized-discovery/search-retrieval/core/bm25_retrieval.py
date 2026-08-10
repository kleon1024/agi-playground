"""BM25 retrieval over a small document set, from scratch.

Search retrieval is the same cascade as recommendation recall: a cheap,
scalable first stage that returns a candidate set a heavier ranker later
re-orders. This stage builds BM25 from scratch — the lexical baseline
every dense-retrieval paper compares against — over a small synthetic
corpus, and measures the classic failure: vocabulary mismatch (a query
word absent from the document scores zero).

Run:
    uv run python core/bm25_retrieval.py
    uv run python core/bm25_retrieval.py --emit-log /tmp/bm25-envelope.json

The `--emit-log` flag writes the audit corpus, per-query rankings, and
per-document term overlap so the production path in `prod/bm25_audit.py`
can measure recall against declared relevance — the way a search team
checks where the lexical index loses documents.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

DOCS = {
    "doc1": "wireless headphones noise cancelling bluetooth",
    "doc2": "over ear headphones comfortable long battery",
    "doc3": "running shoes lightweight breathable",
    "doc4": "iphone pro max camera battery life",
    "doc5": "headphones price comparison review 2026",
}

# The audit corpus: the five console docs plus synonym and tail docs, so
# recall can be measured where the lexical index is expected to fail.
AUDIT_DOCS = {
    "d1": "wireless headphones noise cancelling bluetooth",
    "d2": "over ear headphones comfortable long battery",
    "d3": "running shoes lightweight breathable",
    "d4": "iphone pro max camera battery life",
    "d5": "headphones price comparison review 2026",
    "d6": "affordable bluetooth earbuds budget friendly",
    "d7": "sneakers athletic footwear lightweight running",
    "d8": "laptop notebook ultrabook battery life",
    "d9": "cheap headphones deals sale",
}

# (query, declared relevant docs, frequency class) — the relevance labels a
# search team would hold for a logged query set.
AUDIT_QUERIES = [
    ("wireless headphones", ["d1"], "head"),
    ("running shoes", ["d3", "d7"], "head"),
    ("iphone camera", ["d4"], "head"),
    ("laptop battery", ["d8"], "head"),
    ("cheap headphones", ["d9", "d6"], "tail"),
]

K1, B = 1.5, 0.75


def _tokens(text: str) -> list[str]:
    return text.lower().split()


def bm25(query: str, docs: dict[str, str], k1: float = K1, b: float = B) -> list[tuple[str, float]]:
    doc_len = {d: len(_tokens(t)) for d, t in docs.items()}
    avg_len = sum(doc_len.values()) / len(doc_len)
    n = len(docs)
    df: Counter[str] = Counter()
    for d, t in docs.items():
        df.update(set(_tokens(t)))
    scores = {}
    for d, text in docs.items():
        tf = Counter(_tokens(text))
        score = 0.0
        for term in _tokens(query):
            if term not in tf:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            f = tf[term]
            denom = f + k1 * (1 - b + b * doc_len[d] / avg_len)
            score += idf * (f * (k1 + 1)) / denom
        scores[d] = score
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def render() -> None:
    for q in ("wireless headphones", "running shoes", "iphone camera", "headphones 2026"):
        print(f"query: '{q}'")
        for doc, score in bm25(q, DOCS):
            print(f"  {doc:<6} {score:.4f}  {DOCS[doc]}")
        print()
    print("reading: BM25 scores by term frequency with length normalization.")
    print("The vocabulary-mismatch failure is visible: a query word absent")
    print("from a document contributes zero, so lexical retrieval misses")
    print("synonyms — the gap dense retrieval exists to close.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-log", help="write audit corpus and rankings as JSON")
    args = parser.parse_args()
    render()
    if args.emit_log:
        envelope = {
            "docs": AUDIT_DOCS,
            "queries": [
                {
                    "query": q,
                    "relevant": relevant,
                    "freq": freq,
                    "ranking": bm25(q, AUDIT_DOCS),
                    "overlap": {
                        d: len(set(_tokens(q)) & set(_tokens(text)))
                        for d, text in AUDIT_DOCS.items()
                    },
                }
                for q, relevant, freq in AUDIT_QUERIES
            ],
        }
        Path(args.emit_log).write_text(json.dumps(envelope))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
