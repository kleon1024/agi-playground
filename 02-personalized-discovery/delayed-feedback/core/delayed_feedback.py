"""Delayed feedback: a conversion that happens tomorrow is labeled a
negative today. Training on everything is fresh but full of false
negatives; the corrected model reweights in-flight samples by how much
conversion mass remains inside the observation window.

Stage 57 introduces the observation window. The run compares
mature-only, naive-all, and false-negative-corrected CVR models on
window-mature test labels.

Run:
    uv run python core/delayed_feedback.py
"""

from __future__ import annotations

import math
import random
from math import exp


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-min(max(z, -30.0), 30.0)))


def log_loss(y: float, p: float) -> float:
    p = min(max(p, 1e-12), 1.0 - 1e-12)
    return -y * math.log(p) - (1.0 - y) * math.log(1.0 - p)


def fit(xs: list[list[float]], ys: list[int], ws: list[float] | None = None, epochs: int = 50) -> list[float]:
    w = [0.0] * 9
    n = len(xs)
    for _ in range(epochs):
        g = [0.0] * 9
        for k, (x, y) in enumerate(zip(xs, ys)):
            wgt = 1.0 if ws is None else ws[k]
            p = sigmoid(sum(w[i] * x[i] for i in range(8)))
            e = (p - y) * wgt
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
    rng = random.Random(13)
    wc = [rng.uniform(-0.5, 0.5) for _ in range(8)]
    n = 6000
    xs = [[rng.gauss(0, 1) for _ in range(8)] for _ in range(n)]
    conv = [1 if rng.random() < sigmoid(sum(wc[i] * x[i] for i in range(8)) - 1.8) else 0 for x in xs]
    lam = 1 / 4.0
    delay = [rng.expovariate(lam) + 0.5 for _ in range(n)]  # mean ~4.5d
    age = [rng.uniform(0.3, 3.0) for _ in range(n)]  # young snapshot at cut

    window = 7.0
    mature = [i for i in range(n) if age[i] >= window]
    observed = [conv[i] * (1 if delay[i] <= age[i] else 0) for i in range(n)]
    y_window = [conv[i] * (1 if delay[i] <= window else 0) for i in range(n)]

    tr = range(4500)
    te = range(4500, n)

    # (a) mature-only: clean labels within the window, but with a young
    #     snapshot there is no mature set to wait for.
    mtr = [i for i in tr if i in mature]
    w_mature = fit([xs[i] for i in mtr], [y_window[i] for i in mtr]) if mtr else None

    # (b) naive-all: fresh in-flight converters counted as negative.
    w_naive = fit([xs[i] for i in tr], [observed[i] for i in tr])

    # (c) corrected: a censored row gets a soft label
    #     P(delay <= window | delay > age) x base rate under the
    #     exponential delay model — no oracle, only the delay
    #     distribution and the deployed base conversion rate.
    rho = 0.14  # historical base conversion rate
    y_soft = []
    for i in tr:
        if observed[i] == 1:
            y_soft.append(1.0)
        else:
            w = 1.0 - exp(-lam * max(window - age[i], 0.0))
            y_soft.append(min(w * rho, 1.0))
    w_corr = fit([xs[i] for i in tr], y_soft)

    mte = list(te)
    y_te = [y_window[i] for i in mte]
    young = [i for i in mte if age[i] < 2.0]
    truth = sum(y_window[i] for i in young) / len(young)
    print("delayed feedback, read (window 7d, young snapshot 0.3-3d):")
    for name, w in (("mature-only", w_mature), ("naive-all", w_naive), ("corrected", w_corr)):
        if w is None:
            print(f"  {name:<12} starved (no mature rows yet)")
        else:
            ps = [predict(w, xs[i]) for i in mte]
            p_young = sum(predict(w, xs[i]) for i in young) / len(young)
            print(f"  {name:<12} conv auc {auc(ps, y_te):.3f}   pred on fresh {p_young:.3f}")

    n_train = len(tr)
    n_mature = len(mtr)
    n_inflight = sum(1 for i in tr if conv[i] and delay[i] > age[i])
    print()
    print(f"training rows {n_train}, mature rows {n_mature}, in-flight converters {n_inflight}")
    print(f"true conversion-by-7 on fresh traffic: {truth:.3f}")
    print("reading: with a young snapshot there is no mature set to wait for,")
    print("so mature-only is starved by definition. naive-all eats every")
    print("in-flight converter as a false negative and under-reads fresh")
    print("traffic — the CVR dip every launch sees. the corrected model keeps")
    print("all rows and gives censored rows a soft label from the delay")
    print("distribution and the base rate, so freshness stops costing scale.")


if __name__ == "__main__":
    main()
