"""Query correction by edit distance, read: the typo that breaks BM25.

Stage 19 expands the query before retrieval. This script corrects a
misspelled query against a small dictionary and shows the retrieval
consequence of correcting or not.

Run:
    uv run python core/edit_distance.py
"""

from __future__ import annotations


def edit_distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(
                prev[j] + 1,
                cur[j - 1] + 1,
                prev[j - 1] + (ca != cb),
            ))
        prev = cur
    return prev[-1]


def main() -> None:
    vocab = ["headphones", "headsets", "shoes", "shorts", "flights"]
    query = "heaphones"
    matches = sorted(vocab, key=lambda w: edit_distance(query, w))
    print("query correction, read:")
    for word in matches:
        print(f"  {query} -> {word}: distance {edit_distance(query, word)}")
    corrected = matches[0]
    print(f"\n  corrected query: {corrected}")
    print("\nreading: BM25 on the raw query matches nothing in the index;")
    print("the corrected query matches the catalog. Correction is retrieval")
    print("pre-processing — its value is measured by the recall it recovers.")


if __name__ == "__main__":
    main()
