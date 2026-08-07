"""Hallucinated ID, read: the emitted ID that does not exist.

Stage 35 generates document IDs. This script reads the failure where
the generator emits an ID outside the corpus.

Run:
    uv run python core/hallucinated_id.py
"""

from __future__ import annotations


def main() -> None:
    corpus = {"doc_01", "doc_02", "doc_03", "doc_04"}
    generated = ["doc_02", "doc_99", "doc_03"]
    print("hallucinated id, read:")
    for doc_id in generated:
        exists = doc_id in corpus
        print(f"  generated {doc_id}: in corpus {exists}")
    valid = [d for d in generated if d in corpus]
    print(f"  valid results: {valid}")
    print("\nreading: doc_99 is emitted but does not exist, so the beam")
    print("slot is wasted and the result is dropped at the corpus check.")
    print("A retrieval model that manufactures IDs needs the check — the")
    print("index is the arbiter of what the generator may return.")


if __name__ == "__main__":
    main()
