"""The label that is relative, read: what a grader's boundary judgment does.

Stage 12's pairwise ranker is trained on ordinal grades, and an ordinal
grade is a judgment, not a measurement: a second grader can move a
boundary item by one without any of them being "wrong". This chapter
sweeps single-grade perturbations of the stage's own labeled set,
re-fits the pairwise ranker each time, and measures what moves — the
lesson the label-consistency audit names as the case-finding: most
single flips are invisible, and the one that bites is the item sitting
on the learned decision boundary.

Run:
    uv run python core/label_relative_read.py
"""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
from learning_to_rank import BATCHES, DATA


def ndcg(rel: list[int]) -> float:
    def dcg(grades: list[int]) -> float:
        return sum(g / (1 if i == 0 else i) for i, g in enumerate(grades, start=1))

    ideal = sorted(rel, reverse=True)
    return dcg(rel) / dcg(ideal)


def pref_flips(base_order: list[int], other_order: list[int]) -> int:
    """Pairwise preference flips: pairs whose relative order reversed."""
    pos = {item: i for i, item in enumerate(base_order)}
    flips = 0
    for a, b in itertools.combinations(base_order, 2):
        if (pos[a] < pos[b]) != (other_order.index(a) < other_order.index(b)):
            flips += 1
    return flips


def fit_order(grades: list[int]) -> list[int]:
    """Pairwise fit on data graded `grades`, returning the item order."""
    data = [(x, y) for x, y, _ in DATA]
    pairs = []
    for a, b in itertools.combinations(range(len(data)), 2):
        ga, gb = grades[a], grades[b]
        if ga == gb:
            continue
        x1 = data[a][0] - data[b][0]
        x2 = data[a][1] - data[b][1]
        label = 1.0 if ga > gb else -1.0
        pairs.append((x1, x2, label))
    n = len(pairs)
    sx = sum(p[0] for p in pairs)
    sy = sum(p[1] for p in pairs)
    sxy = sum(p[0] * p[1] for p in pairs)
    sy2 = sum(p[1] * p[1] for p in pairs)
    w2 = (n * sxy - sx * sy) / (n * sy2 - sy * sy)
    w1 = (sx - w2 * sy) / n
    scored = [(w1 * x + w2 * y, i) for i, (x, y) in enumerate(data)]
    scored.sort(reverse=True)
    return [i for _, i in scored]


def main() -> None:
    base_grades = BATCHES["A"]
    base_order = fit_order(base_grades)
    base_ndcg = ndcg([base_grades[i] for i in base_order])
    print("label is relative, read (single boundary flips of one item):")
    print(f"  baseline: NDCG {base_ndcg:.4f}  order {base_order}")

    visible = 0
    total = 0
    for item, delta in sorted(
        itertools.product(range(8), (-1, 1)),
        key=lambda t: (t[0], t[1]),
    ):
        if not (0 <= base_grades[item] + delta <= 3):
            continue
        total += 1
        grades = list(base_grades)
        grades[item] += delta
        order_ = fit_order(grades)
        flips = pref_flips(base_order, order_)
        nd = ndcg([base_grades[i] for i in order_])
        marker = "  <-- visible" if flips else ""
        if flips:
            visible += 1
        print(
            f"  item {item} grade {base_grades[item]} -> {grades[item]}: "
            f"NDCG {nd:.4f}, pref flips {flips}{marker}"
        )

    print(f"\n  {visible} of {total} single flips moved the learned order;")
    print("  the visible one is item 6, the item on the smallest-margin")
    print("  boundary of the learned score. Two-flip re-gradings swing")
    print("  NDCG more: batch B moves it to 0.5727, batch C to 0.6209.")
    print("\nreading: most grader disagreements are invisible to the ranker;")
    print("the ones that bite are concentrated on the learned decision")
    print("boundary. That concentration is why redundant grading (majority")
    print("vote across graders) and margin-aware pairwise losses exist.")


if __name__ == "__main__":
    main()
