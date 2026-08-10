"""When the propensity is noisy: inverse-propensity weights are high
variance; a rare item whose exposure estimate is off by 10x gets a
weight that swamps the batch.

Run:
    uv run python core/noisy_propensity.py
"""

from __future__ import annotations

import math
import random


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-min(max(z, -30.0), 30.0)))


def fit(xs: list[list[float]], ys: list[int], ws: list[float] | None = None, epochs: int = 40) -> list[float]:
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
            w[i] -= 0.08 * g[i] / n
    return w


def predict(w: list[float], x: list[float]) -> float:
    return sigmoid(sum(w[i] * x[i] for i in range(8)) + w[8])


def main() -> None:
    rng = random.Random(43)
    wq = [rng.uniform(-0.4, 0.4) for _ in range(8)]
    items = [[rng.gauss(0, 1) for _ in range(8)] for _ in range(400)]
    q = [sigmoid(sum(wq[i] * x[i] for i in range(8))) for x in items]
    expo = [min(1.0, max(0.02, 0.08 + 1.2 * v)) for v in q]

    def build(noise: float, cap: float) -> tuple[list[float], float, float]:
        xs, ys, ws = [], [], []
        for _ in range(8000):
            idx = rng.randrange(len(items))
            prop = expo[idx] * (1.0 + noise * rng.gauss(0, 1)) if noise else expo[idx]
            prop = max(prop, 1e-4)
            wgt = min(1.0 / prop, cap)
            click = 1 if rng.random() < q[idx] else 0
            xs.append(items[idx])
            ys.append(click)
            ws.append(wgt)
        w = fit(xs, ys, ws)
        return [predict(w, x) for x in items], sum(ws) / len(ws), max(ws)

    p_exact, avg_exact, max_exact = build(0.0, 1e6)
    p_noisy, avg_noisy, max_noisy = build(0.5, 1e6)
    p_capped, avg_cap, max_cap = build(0.5, 20.0)

    def corr(a: list[float], b: list[float]) -> float:
        n = len(b)
        ra = sorted(range(n), key=lambda i: a[i])
        rb = sorted(range(n), key=lambda i: b[i])
        pos = {item: k for k, item in enumerate(rb)}
        d2 = sum((pos[i] - ra.index(i)) ** 2 for i in range(n))
        return 1.0 - 6.0 * d2 / (n * (n * n - 1))

    print("when the propensity is noisy, read (variance of IPS weights):")
    print(f"  exact props     mean w {avg_exact:6.1f}  max w {max_exact:8.1f}  corr {corr(p_exact, q):.3f}")
    print(f"  noisy props     mean w {avg_noisy:6.1f}  max w {max_noisy:8.1f}  corr {corr(p_noisy, q):.3f}")
    print(f"  noisy + cap 20  mean w {avg_cap:6.1f}  max w {max_cap:8.1f}  corr {corr(p_capped, q):.3f}")
    print()
    print("reading: the inverse of a noisy small propensity is a huge weight, so")
    print("a handful of rows steer the fit. capping the weight trades a little")
    print("unbiasedness for a lot of variance and recovers the correlation;")
    print("in production the propensity model is itself logged and audited.")


if __name__ == "__main__":
    main()
