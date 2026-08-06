"""Query understanding: tokenize, normalize, and classify a query.

Search begins with the query, and the query is a string with noise:
case, punctuation, stopwords, misspellings, and no explicit intent. This
stage builds the minimal query-understanding pipeline — tokenize,
normalize, classify — and measures what each step does to a small set of
realistic queries. Deterministic, stdlib-only.

Run:
    uv run python core/query_understanding.py
"""

from __future__ import annotations

import re
from collections import Counter

STOPWORDS = {"the", "a", "an", "and", "or", "for", "of", "to", "in", "on"}

QUERIES = [
    "best wireless headphones 2026",
    "buy iPhone 17 Pro Singapore",
    "how to fix sleep schedule",
    "Nike Air Max size 9",
    "cheap flights SIN to NRT",
    "redmi note 13 vs poco x6",
]


def tokenize(q: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", q.lower())


def normalize(tokens: list[str]) -> list[str]:
    return [t for t in tokens if t not in STOPWORDS]


def classify(tokens: list[str]) -> str:
    joined = " ".join(tokens)
    if any(w in joined for w in ("buy", "cheap", "price", "deal", "order")):
        return "transactional"
    if any(w in joined for w in ("how", "why", "what is", "fix", "vs")):
        return "informational"
    return "navigational"


def main() -> None:
    print("query understanding, read per query:")
    for q in QUERIES:
        raw = tokenize(q)
        norm = normalize(raw)
        intent = classify(norm)
        print(f"  '{q}'")
        print(f"    raw {raw} -> normalized {norm} -> {intent}")
    all_tokens = [t for q in QUERIES for t in normalize(tokenize(q))]
    print(f"\n  vocabulary across {len(QUERIES)} queries: {len(set(all_tokens))} terms")
    print(f"  most frequent: {Counter(all_tokens).most_common(5)}")
    print("\nreading: normalization removes the noise that would split the")
    print("index (the/A/The all map to one key), and intent classification")
    print("decides which retrieval path — navigational needs exact, ")
    print("transactional needs price, informational needs coverage.")


if __name__ == "__main__":
    main()
