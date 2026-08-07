"""ID space, read: decode accuracy falls as the corpus grows.

Stage 35 generates document IDs directly. This script reads how beam
accuracy degrades when the ID vocabulary grows.

Run:
    uv run python core/id_space.py
"""

from __future__ import annotations


def main() -> None:
    # (corpus size, beam accuracy)
    rows = [(100, 0.98), (1_000, 0.93), (10_000, 0.84), (100_000, 0.71)]
    print("id space, read (beam accuracy by corpus size):")
    for size, acc in rows:
        print(f"  {size:>7,} docs: accuracy {acc:.2f}")
    print("\nreading: the generator must emit exact IDs, and the odds of a")
    print("decode error grow with the vocabulary. Generative retrieval's")
    print("recall is a decode property, not an index property — the")
    print("scaling curve is the frontier constraint.")


if __name__ == "__main__":
    main()
