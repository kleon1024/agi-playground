"""The stale model, read: freshness is part of ranking quality.

Stage 04's fine-rank model is trained on logged interactions. This script
simulates the distribution shifting after training and reads the NDCG
decay of a model that is not refreshed.

Run:
    uv run python core/stale_read.py
"""

from __future__ import annotations


def ndcg(ranks: list[int]) -> float:
    """NDCG over a list of grades (3=perfect, 0=irrelevant)."""
    ideal = sum((2 ** g - 1) / (i + 2) for i, g in
                enumerate(sorted(ranks, reverse=True)))
    actual = sum((2 ** g - 1) / (i + 2) for i, g in enumerate(ranks))
    return actual / ideal if ideal else 0.0


def main() -> None:
    # True per-item grades by day. The model's score order is frozen at
    # day 0 (item 0 best); as the best item decays and a lower one rises,
    # the frozen order ranks an increasingly wrong list.
    grades_by_day = [
        [3, 2, 2, 1, 1, 0, 0, 0],
        [1, 2, 2, 1, 1, 3, 0, 0],
        [0, 1, 2, 1, 2, 3, 1, 0],
        [0, 1, 0, 1, 2, 3, 2, 1],
        [0, 0, 0, 1, 1, 3, 3, 2],
    ]
    score_order = sorted(range(8), key=lambda i: -grades_by_day[0][i])
    print("stale model, read (NDCG by days since training):")
    for day, grades in enumerate(grades_by_day):
        grades_by_score = [grades[i] for i in score_order]
        print(f"  day {day}: NDCG {ndcg(grades_by_score):.3f}")
    print("\nreading: the model's ranking is a snapshot of the distribution")
    print("it trained on. As the distribution moves, the same score order")
    print("ranks a worse list — freshness is a ranking property, not a")
    print("deployment nicety.")


if __name__ == "__main__":
    main()
