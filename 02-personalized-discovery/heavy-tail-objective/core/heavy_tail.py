"""Heavy-tail objective: GMV is mostly zero with a few whale orders,
so raw MSE is a few samples' argument. The run compares raw MSE, a
log transform, and the decomposed P(order) x E(gmv | order) read, and
measures how much of the gradient the top 1% of samples own.

Stage 60 introduces objective factorization for heavy-tail money.

Run:
    uv run python core/heavy_tail.py
"""

from __future__ import annotations

import math
import random


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-min(max(z, -30.0), 30.0)))


def lin(xs: list[list[float]], ys: list[float], epochs: int = 45) -> list[float]:
    w = [0.0] * 9
    n = len(xs)
    for _ in range(epochs):
        g = [0.0] * 9
        for x, y in zip(xs, ys):
            pred = sum(w[i] * x[i] for i in range(8)) + w[8]
            e = pred - y
            for i in range(8):
                g[i] += e * x[i]
            g[8] += e
        for i in range(9):
            w[i] -= 0.05 * g[i] / n
    return w


def lin_pred(w: list[float], x: list[float]) -> float:
    return sum(w[i] * x[i] for i in range(8)) + w[8]


def fit_logistic(xs: list[list[float]], ys: list[int], epochs: int = 50) -> list[float]:
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


def main() -> None:
    rng = random.Random(53)
    wo = [rng.uniform(-0.5, 0.5) for _ in range(8)]
    wa = [rng.uniform(-0.3, 0.3) for _ in range(8)]
    n = 30000
    xs = [[rng.gauss(0, 1) for _ in range(8)] for _ in range(n)]
    p_order = [sigmoid(sum(wo[i] * x[i] for i in range(8)) - 1.2) for x in xs]
    order = [1 if rng.random() < p else 0 for p in p_order]
    amount = [0.0 if o == 0 else math.exp(2.2 + sum(wa[i] * x[i] for i in range(8)) + rng.gauss(0, 1.2)) for o, x in zip(order, xs)]
    gmv = [o * a for o, a in zip(order, amount)]

    tr = range(24000)
    te = range(24000, n)
    # (a) raw MSE regression on gmv
    w_raw = lin([xs[i] for i in tr], [gmv[i] for i in tr])
    # (b) log(1+gmv) regression
    w_log = lin([xs[i] for i in tr], [math.log1p(gmv[i]) for i in tr])
    # (c) decompose: p(order) logistic + E(amount|order) linear on orders
    w_po = fit_logistic([xs[i] for i in tr], [order[i] for i in tr])
    ord_tr = [i for i in tr if order[i]]
    w_amt = lin([xs[i] for i in ord_tr], [math.log(amount[i]) for i in ord_tr])
    # lognormal correction: E[amount] = exp(mu + sigma^2 / 2)
    resid = [math.log(amount[i]) - lin_pred(w_amt, xs[i]) for i in ord_tr]
    sigma2 = sum(r * r for r in resid) / len(resid)

    def rel_err(pred: list[float]) -> float:
        return sum(abs(p - g) for p, g in zip(pred, [gmv[i] for i in te])) / max(sum(gmv[i] for i in te), 1e-9)

    pred_raw = [max(lin_pred(w_raw, xs[i]), 0.0) for i in te]
    pred_log = [math.expm1(lin_pred(w_log, xs[i])) for i in te]
    pred_dec = [
        sigmoid(lin_pred(w_po, xs[i])) * math.exp(lin_pred(w_amt, xs[i]) + sigma2 / 2) for i in te
    ]

    # whale gradient share: top-1% gmv rows' share of per-row |residual|
    gm = [gmv[i] for i in tr]
    top = set(sorted(range(len(gm)), key=lambda i: gm[i])[-int(len(gm) * 0.01):])

    def whale_share(resids: list[float]) -> float:
        tot = sum(abs(r) for r in resids)
        return sum(abs(resids[i]) for i in top) / max(tot, 1e-9)

    res_raw = [lin_pred(w_raw, xs[i]) - gmv[i] for i in tr]
    res_log = [lin_pred(w_log, xs[i]) - math.log1p(gmv[i]) for i in tr]

    print("heavy-tail objective, read (gmv regression variants):")
    print(f"  {'method':<14}{'rel err':>10}{'whale grad share':>18}")
    print(f"  {'raw mse':<14}{rel_err(pred_raw):>10.3f}{whale_share(res_raw):>18.1%}")
    print(f"  {'log(1+gmv)':<14}{rel_err(pred_log):>10.3f}{whale_share(res_log):>18.1%}")
    print(f"  {'decomposed':<14}{rel_err(pred_dec):>10.3f}{'-':>18}")
    print()
    print("reading: raw MSE fits the whale rows, whose residual owns a fifth")
    print("of the gradient; the log transform cuts that to a twentieth. the")
    print("decomposition lands between the two on pure error but splits the")
    print("problem into a binary order probability and a conditional amount")
    print("regression, so each piece is interpretable and re-tunable on its")
    print("own — its payoff is structure, not the headline number.")


if __name__ == "__main__":
    main()
