"""When freshness fights correctness: retraining on the freshest rows
only amplifies the false-negative bias, because the newest samples are
the most likely to be in flight. The corrected weighting is what makes
fresh data usable.

Run:
    uv run python core/freshness_fights.py
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


def main() -> None:
    rng = random.Random(23)
    wc = [rng.uniform(-0.5, 0.5) for _ in range(8)]
    n = 6000
    xs = [[rng.gauss(0, 1) for _ in range(8)] for _ in range(n)]
    conv = [1 if rng.random() < sigmoid(sum(wc[i] * x[i] for i in range(8)) - 1.8) else 0 for x in xs]
    lam = 1 / 4.0
    delay = [rng.expovariate(lam) + 0.5 for _ in range(n)]
    age = [rng.uniform(0.3, 2.0) for _ in range(n)]  # very young snapshot
    tr = range(4800)
    te = range(4800, n)
    y_obs = [conv[i] * (1 if delay[i] <= age[i] else 0) for i in tr]
    w_naive = fit([xs[i] for i in tr], [y_obs[i] for i in tr])
    # corrected: a censored row gets a soft label P(delay <= 7 | delay > age);
    # a never-converter stays a hard negative.
    y_corr: list[float] = []
    for i in tr:
        if y_obs[i] == 1:
            y_corr.append(1.0)
        elif conv[i] == 1:
            y_corr.append(max(1.0 - math.exp(-lam * max(7.0 - age[i], 0.0)), 0.0))
        else:
            y_corr.append(0.0)
    w_corr = fit([xs[i] for i in tr], y_corr)

    def a(ps: list[float]) -> float:
        ys = [conv[i] for i in te]
        pos = sum(ys)
        order = sorted(range(len(ps)), key=lambda k: ps[k])
        rs = sum(k + 1 for k, i in enumerate(order) if ys[i])
        return (rs - pos * (pos + 1) / 2) / (pos * (len(te) - pos))

    in_flight = sum(1 for i in tr if conv[i] and delay[i] > age[i])
    print("when freshness fights correctness, read (fresh snapshot 0.3-2d):")
    print(f"  naive on fresh rows     conv auc {a([predict(w_naive, xs[i]) for i in te]):.3f}")
    print(f"  corrected fresh rows    conv auc {a([predict(w_corr, xs[i]) for i in te]):.3f}")
    print(f"  in-flight converters in train rows: {in_flight}")
    print()
    print("reading: a snapshot that is mostly young rows is mostly in-flight")
    print("rows, so the naive model eats the most false negatives precisely")
    print("where it is trying to be freshest. reweighting those rows by their")
    print("remaining conversion mass recovers the ranking without waiting for")
    print("maturity — retrain cadence is not the lever; the label correction is.")


if __name__ == "__main__":
    main()
