"""Exposure bias: the model only ever sees what the old model showed.
Not clicked is not the same as not liked when exposure itself is
confounded with the old score and position. The run compares a naive
model on logged interactions, a propensity-weighted (IPS) model, and a
model trained on random-exposure traffic.

Stage 59 introduces the bias family — exposure, position, selection —
and the fix family: propensity weighting and exploration traffic.

Run:
    uv run python core/exposure_bias.py
"""

from __future__ import annotations

import math
import random


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-min(max(z, -30.0), 30.0)))


def fit(xs: list[list[float]], ys: list[int], ws: list[float] | None = None, epochs: int = 45) -> list[float]:
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


def rank_corr(pred_q: list[float], true_q: list[float]) -> float:
    n = len(true_q)
    rp = sorted(range(n), key=lambda i: pred_q[i])
    rt = sorted(range(n), key=lambda i: true_q[i])
    pos = {item: k for k, item in enumerate(rt)}
    d2 = sum((pos[i] - rp.index(i)) ** 2 for i in range(n))
    return 1.0 - 6.0 * d2 / (n * (n * n - 1))


def main() -> None:
    rng = random.Random(41)
    wq = [rng.uniform(-0.4, 0.4) for _ in range(8)]
    m = 1500
    items = [[rng.gauss(0, 1) for _ in range(8)] for _ in range(m)]
    q_true = [sigmoid(sum(wq[i] * x[i] for i in range(8))) for x in items]
    # unobserved popularity confounder: drives exposure and position,
    # but is not part of the features the ranker sees
    u = [rng.gauss(0, 1) for _ in range(m)]
    su = [sigmoid(ui) for ui in u]
    expo = [min(1.0, max(0.02, 0.05 + 1.0 * s)) for s in su]

    def logged_rows(n_rows: int, uniform: bool) -> tuple[list[list[float]], list[int], list[float]]:
        xs, ys, ws = [], [], []
        for _ in range(n_rows):
            idx = rng.randrange(m)
            prop = 1.0 / m if uniform else expo[idx]
            x = items[idx]
            # position boost: popular items get better slots
            boost = 1.0 + 4.0 * su[idx] if not uniform else 1.0
            click = 1 if rng.random() < min(0.99, q_true[idx] * boost) else 0
            xs.append(x)
            ys.append(click)
            ws.append(1.0 / max(prop, 1e-3))
        return xs, ys, ws

    xs_log, ys_log, _ = logged_rows(20000, uniform=False)
    xs_rnd, ys_rnd, _ = logged_rows(20000, uniform=True)
    xs_ips, ys_ips, ws_ips = logged_rows(20000, uniform=False)

    w_naive = fit(xs_log, ys_log)
    w_ips = fit(xs_ips, ys_ips, ws_ips)
    w_rnd = fit(xs_rnd, ys_rnd)

    def corr(w: list[float]) -> float:
        return rank_corr([predict(w, x) for x in items], q_true)

    print("exposure bias, read (confounded exposure vs correction):")
    print(f"  {'model':<14}{'quality rank corr':>18}")
    print(f"  {'naive on log':<14}{corr(w_naive):>18.3f}")
    print(f"  {'propensity (IPS)':<14}{corr(w_ips):>18.3f}")
    print(f"  {'random exposure':<14}{corr(w_rnd):>18.3f}")
    print()
    print("reading: the naive model inherits the old model's exposure, so it")
    print("learns 'shown often' more than 'liked'. weighting each logged row")
    print("by the inverse exposure propensity removes most of the confound;")
    print("random-exposure traffic is the gold reference it is compared to,")
    print("and why exploration traffic is worth real money.")


if __name__ == "__main__":
    main()
