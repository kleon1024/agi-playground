"""Search evaluation: NDCG, MRR, and the metrics' blind spots.

Search evaluation answers "did the ranking work" with a metric, and the
metric choice changes what gets optimized. This stage computes NDCG@k and
MRR on a small result set and shows the classic blind spot: MRR only cares
about the first relevant hit, NDCG weights the top of the list heavily, so
a system can game either by placing one good hit early.

Run:
    uv run python core/search_eval.py
"""

from __future__ import annotations


def ndcg(rel: list[int], k: int | None = None) -> float:
    k = k or len(rel)
    gain = [r / (1 if i == 0 else i) for i, r in enumerate(rel[:k], start=1)]
    ideal = sorted(rel, reverse=True)
    igain = [r / (1 if i == 0 else i) for i, r in enumerate(ideal[:k], start=1)]
    return sum(gain) / sum(igain) if sum(igain) else 0.0


def mrr(rel: list[int]) -> float:
    for i, r in enumerate(rel, start=1):
        if r > 0:
            return 1.0 / i
    return 0.0


def main() -> None:
    rankings = {
        "A: one good hit early": [3, 0, 0, 0, 0],
        "B: good spread": [1, 2, 2, 1, 0],
        "C: good at top": [3, 2, 0, 0, 0],
        "D: reversed": [0, 0, 0, 2, 3],
    }
    print("search evaluation metrics, read:")
    for name, rel in rankings.items():
        print(f"  {name:<22} NDCG@5 {ndcg(rel):.4f}  MRR {mrr(rel):.4f}  rel {rel}")
    print("\nreading: MRR rewards 'first hit early' and ignores the rest;")
    print("NDCG rewards graded relevance weighted to the top. A system can")
    print("inflate MRR by placing one mediocre hit first — the metric's")
    print("blind spot, and why evaluation reports several metrics together.")


if __name__ == "__main__":
    main()
