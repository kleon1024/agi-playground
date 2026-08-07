"""The k in NDCG@k, read: how list length changes the verdict.

NDCG@k is computed over the top k positions. This script computes NDCG@1,
@3, @5 on the same ranking and shows how the metric's verdict changes
with k — a ranking that looks bad at @1 can look good at @5, or vice
versa.

Run:
    uv run python core/k_read.py
"""

from __future__ import annotations


def ndcg(rel: list[int], k: int) -> float:
    gain = [r / (1 if i == 0 else i) for i, r in enumerate(rel[:k], start=1)]
    ideal = sorted(rel, reverse=True)
    igain = [r / (1 if i == 0 else i) for i, r in enumerate(ideal[:k], start=1)]
    return sum(gain) / sum(igain) if sum(igain) else 0.0


def main() -> None:
    rel = [0, 3, 2, 0, 1]
    print("NDCG@k on the same ranking [0,3,2,0,1], read:")
    for k in (1, 3, 5):
        print(f"  NDCG@{k} = {ndcg(rel, k):.3f}")
    print("\nreading: at k=1 the top item is irrelevant (grade 0) so NDCG is")
    print("0; at k=3 the strong hits at 2-3 lift it. The verdict flips with")
    print("k, so k must be declared with the metric — 'NDCG@5' is a different")
    print("claim than 'NDCG@3'.")


if __name__ == "__main__":
    main()
