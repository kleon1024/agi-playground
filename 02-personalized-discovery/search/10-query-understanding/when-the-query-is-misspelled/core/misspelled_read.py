"""The misspelled query, read: what normalization cannot fix.

Query normalization handles case, punctuation, and stopwords, but a
misspelling changes the token itself — 'heaphones' will never match the
indexed 'headphones'. This script runs the stage's own tokenizer over
misspelled variants and shows where normalization stops and spelling
correction must begin.

Run:
    uv run python core/misspelled_read.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
from query_understanding import normalize, tokenize


def main() -> None:
    variants = [
        "wireless headphones",
        "wireless heaphones",
        "wireless hedphones",
        "wirless headphones",
    ]
    index_term = "headphones"
    print("misspelled queries, read:")
    for q in variants:
        tokens = normalize(tokenize(q))
        hit = index_term in tokens
        print(f"  '{q}' -> {tokens}  exact-match on '{index_term}': {hit}")
    print("\nreading: normalization fixes case and stopwords but not")
    print("misspelling — 'heaphones' never becomes 'headphones'. Retrieval")
    print("must either correct the query or match by edit distance, which is")
    print("why spelling correction sits inside query understanding.")


if __name__ == "__main__":
    main()
