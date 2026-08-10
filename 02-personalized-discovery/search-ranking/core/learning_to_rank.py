"""Learning to rank: pointwise regression versus pairwise ranking.

Search ranking re-orders the retrieval candidate set. The two classic
formulations differ in the objective: pointwise predicts a relevance score
per item, pairwise learns which of two items should be first. This stage
implements both from scratch on a small labeled set and compares them by
the metric that matters — NDCG@k, not squared error.

Run:
    uv run python core/learning_to_rank.py
    uv run python core/learning_to_rank.py --emit-log /tmp/ltr-envelope.json

The `--emit-log` flag writes the labeled items plus two re-graded batches
so the production path in `prod/ltr_audit.py` can run the pairwise label-
consistency check — the way a search team compares two grading passes
before trusting an offline NDCG.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# (feature1, feature2, true_grade 0-3) — a small labeled set.
DATA = [
    (1.0, 0.2, 1),
    (0.9, 0.5, 2),
    (0.7, 0.8, 3),
    (0.5, 0.4, 2),
    (0.3, 0.1, 0),
    (0.2, 0.9, 3),
    (0.1, 0.3, 1),
    (0.8, 0.1, 1),
]

# Two plausible re-gradings of the same items (illustrative second
# grading passes): batch B moves the two boundary items at grades 0/1,
# batch C moves a grade-3 and a grade-1 item by one.
BATCHES = {
    "A": [1, 2, 3, 2, 0, 3, 1, 1],
    "B": [1, 2, 3, 2, 1, 3, 1, 0],
    "C": [1, 2, 3, 2, 0, 2, 1, 2],
}


def dcg(rel: list[int], k: int | None = None) -> float:
    k = k or len(rel)
    return sum(r / (1 if i == 0 else i) for i, r in enumerate(rel[:k], start=1))


def ndcg(rel: list[int]) -> float:
    ideal = sorted(rel, reverse=True)
    return dcg(rel) / dcg(ideal) if dcg(ideal) else 0.0


def pointwise(data: list[tuple[float, float, int]]) -> list[int]:
    """Rank by a learned linear score w1*x1 + w2*x2 (fit by least squares)."""
    n = len(data)
    sx = sum(x for x, _, _ in data)
    sy = sum(y for _, y, _ in data)
    sxy = sum(x * y for x, y, _ in data)
    sy2 = sum(y * y for _, y, _ in data)
    w2 = (n * sxy - sx * sy) / (n * sy2 - sy * sy)
    w1 = (sx - w2 * sy) / n
    scored = [(w1 * x + w2 * y, i) for i, (x, y, _) in enumerate(data)]
    scored.sort(reverse=True)
    return [i for _, i in scored]


def pairwise(data: list[tuple[float, float, int]]) -> list[int]:
    """Rank by a learned pairwise preference (linear, margin-0 least squares on pairs)."""
    import itertools as it

    pairs = []
    for a, b in it.combinations(range(len(data)), 2):
        ga, gb = data[a][2], data[b][2]
        if ga == gb:
            continue
        x1 = data[a][0] - data[b][0]
        x2 = data[a][1] - data[b][1]
        label = 1.0 if ga > gb else -1.0
        pairs.append((x1, x2, label))
    # linear score s = w1*x1 + w2*x2 fit by least squares to the pair labels.
    n = len(pairs)
    sx = sum(p[0] for p in pairs)
    sy = sum(p[1] for p in pairs)
    sxy = sum(p[0] * p[1] for p in pairs)
    sy2 = sum(p[1] * p[1] for p in pairs)
    w2 = (n * sxy - sx * sy) / (n * sy2 - sy * sy)
    w1 = (sx - w2 * sy) / n
    scored = [(w1 * x + w2 * y, i) for i, (x, y, _) in enumerate(data)]
    scored.sort(reverse=True)
    return [i for _, i in scored]


def render() -> None:
    true = [g for _, _, g in DATA]
    for name, ranker in (("pointwise", pointwise), ("pairwise", pairwise)):
        order = ranker(DATA)
        rel = [true[i] for i in order]
        print(f"{name:<10} NDCG {ndcg(rel):.4f}  order {order}")
    print("\nreading: both learn a linear score, but pairwise optimizes the")
    print("comparison that search cares about — 'is A before B' — while")
    print("pointwise optimizes absolute score. On small data they often agree;")
    print("the NDCG gap is where the formulations diverge.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-log", help="write the labeled set and batches as JSON")
    args = parser.parse_args()
    render()
    if args.emit_log:
        envelope = {
            "data": [{"x1": x, "x2": y, "grade": g} for x, y, g in DATA],
            "batches": BATCHES,
        }
        Path(args.emit_log).write_text(json.dumps(envelope))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
