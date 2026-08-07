"""What MRR cannot see, read on three rankings.

MRR records only the position of the first relevant hit, so it is blind
to everything below it. This script shows three rankings that differ
dramatically in quality yet are indistinguishable to MRR — the case that
forces NDCG (or a graded metric) into the evaluation.

Run:
    uv run python core/metric_disagree.py
"""

from __future__ import annotations


def ndcg(rel: list[int]) -> float:
    gain = [r / (1 if i == 0 else i) for i, r in enumerate(rel, start=1)]
    ideal = sorted(rel, reverse=True)
    igain = [r / (1 if i == 0 else i) for i, r in enumerate(ideal, start=1)]
    return sum(gain) / sum(igain) if sum(igain) else 0.0


def mrr(rel: list[int]) -> float:
    for i, r in enumerate(rel, start=1):
        if r > 0:
            return 1.0 / i
    return 0.0


def main() -> None:
    rankings = {
        "one perfect hit, rest empty": [3, 0, 0, 0, 0],
        "strong hits, mis-ordered": [3, 0, 2, 0, 2],
        "mediocre hits, mis-ordered": [3, 0, 1, 0, 1],
    }
    print("what MRR cannot see, read:")
    for name, rel in rankings.items():
        print(f"  {name:<32} NDCG {ndcg(rel):.3f}  MRR {mrr(rel):.3f}")
    print("\nreading: all three rank identically on MRR (1.0) because the")
    print("first hit is at position 1, while NDCG separates them (1.000 vs")
    print("0.871 vs 0.922) by how the relevant material below is graded")
    print("and placed — MRR is blind to everything after the first hit.")
    print("The blind spot is why graded, top-weighted metrics exist.")


if __name__ == "__main__":
    main()
