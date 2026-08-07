"""When correction helps, read: recall recovered by the fix.

Stage 19 corrects queries before retrieval. This script scores retrieval
with and without correction over a small corpus.

Run:
    uv run python core/correction_helps.py
"""

from __future__ import annotations


def hits(query: str, docs: list[str]) -> int:
    return sum(1 for d in docs if query in d)


def main() -> None:
    docs = [
        "wireless headphones review",
        "headphones for running",
        "over-ear headphones",
        "headset for calls",
    ]
    raw = "heaphones"
    fixed = "headphones"
    print("correction helps, read:")
    print(f"  raw query '{raw}': {hits(raw, docs)} document hits")
    print(f"  corrected '{fixed}': {hits(fixed, docs)} document hits")
    print("\nreading: the raw query retrieves nothing, the corrected one")
    print("finds three documents. The correction's value is the recall it")
    print("recovers — a retrieval-side metric, not a query-side nicety.")


if __name__ == "__main__":
    main()
