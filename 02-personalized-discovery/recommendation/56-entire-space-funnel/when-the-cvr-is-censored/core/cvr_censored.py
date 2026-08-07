"""When the CVR is censored: training the pay head only on clicked
samples hides the funnel's lower levels. The censored head can only
rank pay inside the clicked population; the full-space head learns
the same conditional on every impression and ranks the whole funnel.

Run:
    uv run python core/cvr_censored.py
"""

from __future__ import annotations

import math
import random


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-min(max(z, -30.0), 30.0)))


def fit(xs: list[list[float]], ys: list[int], epochs: int = 50) -> list[float]:
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


def predict(w: list[float], x: list[float]) -> float:
    return sigmoid(sum(w[i] * x[i] for i in range(8)) + w[8])


def auc(ps: list[float], ys: list[int]) -> float:
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    pos = sum(ys)
    neg = len(ys) - pos
    if pos == 0 or neg == 0:
        return 0.5
    rs = sum(k + 1 for k, i in enumerate(order) if ys[i])
    return (rs - pos * (pos + 1) / 2) / (pos * neg)


def main() -> None:
    rng = random.Random(11)
    wc = [rng.uniform(-0.4, 0.4) for _ in range(8)]
    wp = [0.7 * wi + rng.gauss(0, 0.15) for wi in wc]
    n = 6000
    xs = [[rng.gauss(0, 1) for _ in range(8)] for _ in range(n)]
    click = [1 if rng.random() < sigmoid(sum(wc[i] * x[i] for i in range(8))) else 0 for x in xs]
    pay = [c * (1 if rng.random() < sigmoid(sum(wp[i] * x[i] for i in range(8)) - 2.5) else 0) for c, x in zip(click, xs)]
    tr = range(4800)
    te = range(4800, n)
    cl_tr = [i for i in tr if click[i]]
    w_cen = fit([xs[i] for i in cl_tr], [pay[i] for i in cl_tr])
    w_full = fit([xs[i] for i in tr], [pay[i] for i in tr])
    yh = [pay[i] for i in te]
    print("when the cvr is censored, read (pay head on clicked subset vs full space):")
    print(f"  censored head     pay auc {auc([predict(w_cen, xs[i]) for i in te], yh):.3f}  positives {sum(pay[i] for i in cl_tr)}")
    print(f"  full-space head   pay auc {auc([predict(w_full, xs[i]) for i in te], yh):.3f}  positives {sum(pay[i] for i in tr)}")
    print()
    print("reading: the censored head is trained only on impressions that")
    print("clicked, so its pay ranking is worse than random on the full")
    print("funnel and sees a fraction of the positives. the full-space head")
    print("learns the same conditional on every impression; the pay signal is")
    print("the same, but the ground it is learned on is not. this is the")
    print("censoring ESMM removes by modeling the whole exposure space.")


if __name__ == "__main__":
    main()
