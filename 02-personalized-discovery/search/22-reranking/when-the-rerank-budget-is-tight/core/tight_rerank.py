"""The tight rerank budget, read: k decides what the reranker sees.

Stage 22 reranks only the top k from the first stage. This script reads
what a smaller k costs when a good document sits below the cutoff.

Run:
    uv run python core/tight_rerank.py
"""

from __future__ import annotations


def main() -> None:
    # (doc, first-stage score, reranker score). d5 is ranked 5th by the
    # first stage but would be the reranker's 1st.
    docs = [
        ("d1", 0.99, 0.20), ("d2", 0.98, 0.25), ("d3", 0.97, 0.30),
        ("d4", 0.96, 0.35), ("d5", 0.50, 0.99),
    ]
    for k in (3, 4, 5):
        pool = [d for d, _, _ in sorted(docs, key=lambda x: -x[1])[:k]]
        reachable = "d5" in pool
        print(f"  k={k}: reranker sees top {k}, d5 reachable: {reachable}")
    print("\nreading: with k=3 or 4, d5 never reaches the reranker and its")
    print("0.99 score is never seen. The first stage's cutoff is a filter")
    print("on what the reranker can fix — a tight budget hides recall.")


if __name__ == "__main__":
    main()
