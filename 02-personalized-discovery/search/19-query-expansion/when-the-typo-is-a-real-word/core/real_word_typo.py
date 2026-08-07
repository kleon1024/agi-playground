"""The typo that is a real word, read: the correction that never fires.

Stage 19 corrects queries by edit distance. The failure mode this
chapter reads is the misspelling that is itself a valid catalog term:
the token is in the vocabulary, so distance-based correction never
fires, and the retrieval path serves the wrong category without any
string-level signal that anything went wrong.

Run:
    uv run python core/real_word_typo.py
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
    vocab = ["shoes", "shorts", "shirts", "boots", "socks"]
    query = "shorts"  # intended: shoes
    print("real-word typo, read:")
    print(f"  query '{query}' is a catalog term: {query in vocab}")
    print(f"  nearest edit-distance candidates: {query} (0), "
          f"{sorted(vocab, key=lambda w: edit_distance(query, w))[1]}")
    print("  correction fires: no — the token is already in the vocabulary")
    print("\nreading: string-level correction cannot see this error. The")
    print("query is a real word, so edit distance passes it unchanged and")
    print("BM25 serves shorts to a user who wanted shoes. The evidence")
    print("that it is a typo lives outside the string — the click log and")
    print("query co-occurrence — which is why production correction adds")
    print("log evidence on top of distance.")


if __name__ == "__main__":
    main()
