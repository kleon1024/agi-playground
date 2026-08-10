"""When the distillation blurs: a noisy teacher distills its noise.
The run compares distilling a clean final score against a noisy one.

Run:
    uv run python core/distillation_blurs.py
"""

from __future__ import annotations

import math
import random


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-min(max(z, -30.0), 30.0)))


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


def main() -> None:
    rng = random.Random(79)
    wf = [rng.uniform(-0.4, 0.4) for _ in range(8)]
    m = 1200
    items = [[rng.gauss(0, 1) for _ in range(8)] for _ in range(m)]
    final = [sigmoid(sum(wf[i] * x[i] for i in range(8))) for x in items]
    clean = [f + rng.gauss(0, 0.02) for f in final]
    noisy = [f + rng.gauss(0, 0.25) for f in final]
    w_clean = fit_lin(items, clean)
    w_noisy = fit_lin(items, noisy)

    def corr(pred: list[float]) -> float:
        n = m
        rp = sorted(range(n), key=lambda i: pred[i])
        rt = sorted(range(n), key=lambda i: final[i])
        pos = {item: k for k, item in enumerate(rt)}
        d2 = sum((pos[i] - rp.index(i)) ** 2 for i in range(n))
        return 1.0 - 6.0 * d2 / (n * (n * n - 1))

    print("when the distillation blurs, read (teacher noise):")
    print(f"  clean teacher  distills rank corr {corr([sum(w_clean[i] * x[i] for i in range(8)) + w_clean[8] for x in items]):.3f}")
    print(f"  noisy teacher  distills rank corr {corr([sum(w_noisy[i] * x[i] for i in range(8)) + w_noisy[8] for x in items]):.3f}")
    print()
    print("reading: distillation copies the teacher, mistakes included. a final")
    print("ranker whose scores are themselves noisy — uncalibrated, freshly")
    print("retrained, or evaluated on a small slice — passes that noise to the")
    print("pre-rank. the fix is to distill a stable, calibrated teacher score,")
    print("or to gate which slices are trusted enough to teach.")


if __name__ == "__main__":
    main()
