"""Reranker disagreement, read: two rankers, two orders, one budget.

Stage 22 reranks with a richer model. This script reads how often the two
stages disagree and what the disagreement means for the merged order.

Run:
    uv run python core/reranker_disagrees.py
"""

from __future__ import annotations


def main() -> None:
    # (doc, first, rerank)
    docs = [
        ("d1", 0.98, 0.10), ("d2", 0.97, 0.90), ("d3", 0.50, 0.95),
        ("d4", 0.96, 0.15), ("d5", 0.49, 0.88),
    ]
    first = [d for d, f, r in sorted(docs, key=lambda x: -x[1])]
    rerank = [d for d, f, r in sorted(docs, key=lambda x: -x[2])]
    print("reranker disagreement, read:")
    print(f"  first stage: {first}")
    print(f"  reranker:    {rerank}")
    print(f"  same top-3:  {sorted(first[:3]) == sorted(rerank[:3])}")
    print("\nreading: the first stage ranks by cheap signals, the reranker")
    print("by rich ones, and they disagree on d2/d3. The disagreement is")
    print("the point — if they always agreed, the reranker would be dead")
    print("weight. It is also the risk: the budget only reranks a pool,")
    print("and anything outside it keeps the first stage's verdict.")


if __name__ == "__main__":
    main()
