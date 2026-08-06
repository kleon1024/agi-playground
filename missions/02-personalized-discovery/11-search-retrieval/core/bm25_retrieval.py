"""BM25 retrieval over a small document set, from scratch.

Search retrieval is the same cascade as recommendation recall: a cheap,
scalable first stage that returns a candidate set a heavier ranker later
re-orders. This stage builds BM25 from scratch — the lexical baseline
every dense-retrieval paper compares against — over a small synthetic
corpus, and measures the classic failure: vocabulary mismatch (a query
word absent from the document scores zero).

Run:
    uv run python core/bm25_retrieval.py
"""

from __future__ import annotations

import math
from collections import Counter

DOCS = {
    "doc1": "wireless headphones noise cancelling bluetooth",
    "doc2": "over ear headphones comfortable long battery",
    "doc3": "running shoes lightweight breathable",
    "doc4": "iphone pro max camera battery life",
    "doc5": "headphones price comparison review 2026",
}

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


def main() -> None:
    for q in ("wireless headphones", "running shoes", "iphone camera", "headphones 2026"):
        print(f"query: '{q}'")
        for doc, score in bm25(q, DOCS):
            print(f"  {doc:<6} {score:.4f}  {DOCS[doc]}")
        print()
    print("reading: BM25 scores by term frequency with length normalization.")
    print("The vocabulary-mismatch failure is visible: a query word absent")
    print("from a document contributes zero, so lexical retrieval misses")
    print("synonyms — the gap dense retrieval exists to close.")


if __name__ == "__main__":
    main()
