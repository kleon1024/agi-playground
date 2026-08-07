"""Funnel consistency: using a conditional head as if it were a
marginal reports p(order) above p(click) — a probability contradiction.
The run compares the broken conditional-as-marginal read against the
chained marginal p(click) x p(order|click).

Stage 62 introduces label/probability semantic consistency: the funnel
constraint p(pay) <= p(order) <= p(click) is structural, so the model
should be too.

Run:
    uv run python core/funnel_consistency.py
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


def main() -> None:
    rng = random.Random(71)
    wc = [rng.uniform(-0.5, 0.5) for _ in range(8)]
    wo = [rng.uniform(-0.5, 0.5) for _ in range(8)]
    n = 5000
    xs = [[rng.gauss(0, 1) for _ in range(8)] for _ in range(n)]
    click = [1 if rng.random() < sigmoid(sum(wc[i] * x[i] for i in range(8))) else 0 for x in xs]
    order = [c * (1 if rng.random() < sigmoid(sum(wo[i] * x[i] for i in range(8))) else 0) for c, x in zip(click, xs)]

    tr = range(4000)
    te = range(4000, n)
    w_click = fit([xs[i] for i in tr], [click[i] for i in tr])
    cl_tr = [i for i in tr if click[i]]
    w_oc = fit([xs[i] for i in cl_tr], [order[i] for i in cl_tr])  # conditional head

    viol = 0
    logloss_broken = logloss_chained = 0.0
    for i in te:
        pc = predict(w_click, xs[i])
        poc = predict(w_oc, xs[i])
        broken = poc  # conditional used as if it were the marginal
        chained = pc * poc
        if broken > pc:
            viol += 1
        for p, acc in ((broken, "broken"), (chained, "chained")):
            p = min(max(p, 1e-12), 1 - 1e-12)
            ll = -order[i] * math.log(p) - (1 - order[i]) * math.log(1 - p)
            if acc == "broken":
                logloss_broken += ll
            else:
                logloss_chained += ll
    m = len(te)
    print("funnel consistency, read (conditional-as-marginal vs chained):")
    print(f"  broken read: p(order)>p(click) on {viol}/{m} held-out impressions")
    print(f"  broken read  order logloss {logloss_broken / m:.3f}")
    print(f"  chained read order logloss {logloss_chained / m:.3f}  (violations: 0 by construction)")
    print()
    print("reading: the head trained on clicked impressions estimates")
    print("p(order|click), and using it as p(order|impression) overstates the")
    print("marginal, so the pipeline reports an order probability above a click")
    print("probability. the chained read multiplies the marginal click")
    print("probability by the conditional, which keeps monotonicity structural")
    print("and recovers the marginal the downstream stage actually blends.")


if __name__ == "__main__":
    main()
