"""Fusing candidate sets, read: BM25 plus dense into one list.

Stage 21 combines lexical and dense candidate sets. This script reads
reciprocal rank fusion on two short lists.

Run:
    uv run python core/fuse_sets.py
"""

from __future__ import annotations


def rrf(rankings: list[list[str]], k: int = 60) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking, 1):
            scores[doc] = scores.get(doc, 0.0) + 1.0 / (k + rank)
    return scores


def main() -> None:
    lexical = ["d1", "d2", "d3", "d4"]
    dense = ["d4", "d5", "d1", "d6"]
    fused = rrf([lexical, dense])
    print("hybrid fusion, read (reciprocal rank fusion):")
    for doc, score in sorted(fused.items(), key=lambda kv: -kv[1]):
        where = []
        if doc in lexical:
            where.append(f"lexical#{lexical.index(doc) + 1}")
        if doc in dense:
            where.append(f"dense#{dense.index(doc) + 1}")
        print(f"  {doc}: {score:.4f} ({', '.join(where)})")
    print("\nreading: d4 and d1 appear in both sets and rank highest; d2, d3")
    print("survive only from lexical; d5, d6 only from dense. Fusion keeps")
    print("the union while rewarding documents both matchers agree on.")


if __name__ == "__main__":
    main()
