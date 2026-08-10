"""Phrase IDs, read: a substring can name many documents.

Stage 35 decodes document IDs. The ID format decides how ambiguous a
decode can be: an atomic ID (DSI) names exactly one document, while a
phrase or ngram ID (SEAL) lets the model emit readable substrings that
can match several documents at once. This script counts the ambiguity
in a tiny corpus of titles.

Run:
    uv run python core/phrase_id.py
"""

from __future__ import annotations

CORPUS = [
    "transformer memory as a differentiable search index",
    "autoregressive search engines",
    "search with learned sparse representations",
    "a memory network approach to story comprehension",
    "memory augmented neural networks",
    "long short-term memory",
    "search results personalization",
    "the web as a searchable memory",
]


def named(phrase: str) -> int:
    needle = phrase.lower()
    return sum(1 for title in CORPUS if needle in title.lower())


def main() -> None:
    emitted = ["search", "memory", "transformer memory", "sparse representations"]
    print("phrase id, read (substring match ambiguity):")
    print("  emitted phrase        docs named")
    for phrase in emitted:
        print(f"  {phrase:<20} {named(phrase)}")
    print("\nreading: an atomic ID names one document, so the decode is")
    print("unambiguous. A phrase ID reads naturally but can name many")
    print("documents at once — the model emits 'search' and the corpus")
    print("offers five candidates, so a substring index has to resolve")
    print("which document the phrase meant.")


if __name__ == "__main__":
    main()
