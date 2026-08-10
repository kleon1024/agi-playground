"""The metric that is gamed, read: concentration beats coverage.

Stage 13's metrics have blind spots, and a system can place relevance
exactly where the metric cannot see. MRR is binary: any relevant hit at
position 1 scores 1.0, whether it is a grade-1 near-miss or a grade-3
perfect match. NDCG is top-weighted: a sorted top-3 with an empty tail
normalizes to 1.0. This chapter builds two rankings engineered to win
one metric each, and measures what the other metric says about them.

Run:
    uv run python core/metric_game_read.py
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
    rankings = [
        ("honest spread", [1, 2, 2, 1, 0], "graded relevance spread down the list"),
        ("mrr gamer", [1, 3, 3, 3, 3], "a grade-1 hit placed first; MRR cannot"),
        ("ndcg gamer", [3, 2, 2, 0, 0], "sorted high grades at the top; the"),
        ("both gamed", [3, 0, 0, 0, 0], "one perfect hit, nothing after;"),
    ]
    print("metric game, read (NDCG@5 and MRR per engineered ranking):")
    for name, rel, note in rankings:
        print(f"  {name:<12} NDCG {ndcg(rel):.4f}  MRR {mrr(rel):.4f}  rel {rel}")
    print("\nreading:")
    print("  mrr gamer: MRR 1.0000 — identical to the honest spread — while")
    print("  NDCG drops 0.8140 to 0.7519. MRR is binary: the grade-1 hit at")
    print("  position 1 is worth the same as a grade-3 hit.")
    print("  ndcg gamer: NDCG 1.0000 — the sorted top-3 is the ideal of its")
    print("  own list — while positions 4-5 are empty. The discount makes")
    print("  the tail nearly invisible.")
    print("  both gamed: perfect on both metrics with a single relevant")
    print("  document; nothing after position 1 exists.")
    print("  The fix is the suite plus per-position NDCG@k curves: report")
    print("  several metrics and the rank-gap audit, because the metric")
    print("  being optimized is the one that gets gamed.")


if __name__ == "__main__":
    main()
