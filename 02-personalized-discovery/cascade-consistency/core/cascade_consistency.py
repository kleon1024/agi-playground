"""Cascade consistency: the final ranker optimizes watch + like +
transaction, but a pre-rank trained on CTR kills high-value items
before the expensive model ever sees them. The run compares a
CTR-only pre-rank with one distilled from the final ranker's scores.

Stage 63 introduces the pre-rank/rank objective mismatch and the
teacher-distillation fix.

Run:
    uv run python core/cascade_consistency.py
"""

from __future__ import annotations

import math
import random


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-min(max(z, -30.0), 30.0)))


def fit_log(xs: list[list[float]], ys: list[int], epochs: int = 45) -> list[float]:
    w = [0.0] * 9
    n = len(xs)
    for _ in range(epochs):
        g = [0.0] * 9
        for x, y in zip(xs, ys):
            p = sigmoid(sum(w[i] * x[i] for i in range(8)))
            e = p - y
            for i in range(8):
                g[i] += e * x[i]
            g[8] += e
        for i in range(9):
            w[i] -= 0.1 * g[i] / n
    return w


def fit_lin(xs: list[list[float]], ys: list[float], epochs: int = 45) -> list[float]:
    w = [0.0] * 9
    n = len(xs)
    for _ in range(epochs):
        g = [0.0] * 9
        for x, y in zip(xs, ys):
            p = sum(w[i] * x[i] for i in range(8)) + w[8]
            e = p - y
            for i in range(8):
                g[i] += e * x[i]
            g[8] += e
        for i in range(9):
            w[i] -= 0.05 * g[i] / n
    return w


def pred_log(w: list[float], x: list[float]) -> float:
    return sigmoid(sum(w[i] * x[i] for i in range(8)) + w[8])


def pred_lin(w: list[float], x: list[float]) -> float:
    return sum(w[i] * x[i] for i in range(8)) + w[8]


def main() -> None:
    rng = random.Random(73)
    wf = [rng.uniform(-0.4, 0.4) for _ in range(8)]
    wc = [rng.uniform(-0.4, 0.4) for _ in range(8)]
    m = 1500
    items = [[rng.gauss(0, 1) for _ in range(8)] for _ in range(m)]
    final = [sigmoid(sum(wf[i] * x[i] for i in range(8))) for x in items]
    clicks = [1 if rng.random() < sigmoid(sum(wc[i] * x[i] for i in range(8))) else 0 for x in items]

    # pre-rank models learned on logged data
    w_ctr = fit_log(items, clicks)
    w_dist = fit_lin(items, final)

    k_pre = 100
    k_top = 20

    def report(name: str, scores: list[float]) -> None:
        cut = sorted(range(m), key=lambda i: scores[i], reverse=True)[:k_pre]
        top_final = sorted(range(m), key=lambda i: final[i], reverse=True)[:k_top]
        recall = len(set(cut) & set(top_final)) / k_top
        # ndcg of final scores within the surviving pre-rank cut
        surv = sorted(cut, key=lambda i: final[i], reverse=True)[:k_top]
        dcg = sum(final[surv[k]] / math.log2(k + 2) for k in range(len(surv)))
        ideal = sorted(range(m), key=lambda i: final[i], reverse=True)[:k_top]
        idcg = sum(final[ideal[k]] / math.log2(k + 2) for k in range(len(ideal)))
        print(f"  {name:<18} top-{k_top} recall {recall:.2f}   final ndcg {dcg / max(idcg, 1e-9):.3f}")

    print("cascade consistency, read (pre-rank cut of 100 of 1500):")
    report("ctr-only pre-rank", [pred_log(w_ctr, x) for x in items])
    report("distilled pre-rank", [pred_lin(w_dist, x) for x in items])
    print()
    print("reading: a pre-rank that optimizes clicks quietly discards the")
    print("transaction-heavy items the final ranker would have surfaced, and")
    print("the expensive ranker can only re-rank survivors. distilling the")
    print("final score into the pre-rank — as a soft label instead of a click")
    print("label — keeps the top of the final ranking inside the cut, which is")
    print("the metric that actually matters for the cascade.")


if __name__ == "__main__":
    main()
