"""Reranking, read: the expensive model reorders the top k.

Stage 22 reranks the first stage's top candidates with a richer model.
This script reads the reorder on a small list.

Run:
    uv run python core/rerank_top_k.py
"""

from __future__ import annotations


def main() -> None:
    # (doc, first-stage score, reranker score)
    docs = [
        ("d1", 0.95, 0.30),
        ("d2", 0.90, 0.85),
        ("d3", 0.85, 0.20),
        ("d4", 0.80, 0.92),
        ("d5", 0.75, 0.45),
    ]
    first = [d for d, _, _ in sorted(docs, key=lambda x: -x[1])]
    reranked = [d for d, _, _ in sorted(docs, key=lambda x: -x[2])]
    print("reranking top k, read:")
    print(f"  first stage:  {first}")
    print(f"  reranker:     {reranked}")
    moved = sum(1 for a, b in zip(first, reranked) if a != b)
    print(f"  positions changed: {moved}/5")
    print("\nreading: the reranker reorders using features the first stage")
    print("cannot afford — d4 jumps from 4th to 1st. The first stage")
    print("recalls, the reranker refines; the division is a latency budget")
    print("split, not a preference.")


if __name__ == "__main__":
    main()
