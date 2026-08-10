"""The gain below the fold, read: served k versus eval k.

Stage 22 reranks the first stage's top candidates, and the page serves
only the top three. The failure mode this chapter reads is the reranker
whose fixes land in the middle of the list: offline NDCG@10 says the
reranker helps, the three-slot page sees a top-3 that got worse, and
the improvement the team measured never reaches a user.

Run:
    uv run python core/below_fold_gain.py
"""

from __future__ import annotations


def ndcg(rel: list[int], k: int | None = None) -> float:
    k = k or len(rel)
    gain = [r / i for i, r in enumerate(rel[:k], start=1)]
    ideal = sorted(rel, reverse=True)
    igain = [r / i for i, r in enumerate(ideal[:k], start=1)]
    return sum(gain) / sum(igain) if sum(igain) else 0.0


def main() -> None:
    first = [3, 3, 2, 1, 1, 1, 1, 2, 2, 2]
    rerank = [3, 2, 3, 2, 2, 2, 1, 1, 1, 1]
    print("below-the-fold gain, read (grade lists, 10 positions):")
    print(f"  first stage: {first}")
    print(f"  reranker:    {rerank}")
    print(f"  first  NDCG@10 {ndcg(first, 10):.4f}  NDCG@3 {ndcg(first, 3):.4f}")
    print(f"  rerank NDCG@10 {ndcg(rerank, 10):.4f}  NDCG@3 {ndcg(rerank, 3):.4f}")
    print("\nreading: the reranker promoted a grade-2 buried at position")
    print("10 up to position 4 and fixed the middle of the list — NDCG@10")
    print("improves. To do that it mis-swapped positions 2 and 3, so the")
    print("three-slot page shows a worse top-3 while the offline report")
    print("says the reranker helps. The eval k and the served k disagree;")
    print("report at the served k, audit per position, and never ship a")
    print("reranker on the strength of gains below the fold.")


if __name__ == "__main__":
    main()
