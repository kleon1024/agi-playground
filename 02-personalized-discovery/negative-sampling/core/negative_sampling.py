"""Negative sampling: downsampling negatives makes training tractable
and inflates every predicted probability; the correction factor
restores calibration without touching ranking.

Stage 58 introduces sampling correction. The run trains the same
logistic model on the full set and on a 10x-downsampled negative set,
then applies the classic inverse correction and measures calibration
(ECE) on a held-out set with the true base rate.

Run:
    uv run python core/negative_sampling.py
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


def ece(ps: list[float], ys: list[int], bins: int = 10) -> float:
    width = 1.0 / bins
    total = 0.0
    for b in range(bins):
        lo, hi = b * width, (b + 1) * width
        idx = [k for k, p in enumerate(ps) if lo <= p < hi or (b == bins - 1 and p == 1.0)]
        if not idx:
            continue
        avg_p = sum(ps[k] for k in idx) / len(idx)
        avg_y = sum(ys[k] for k in idx) / len(idx)
        total += len(idx) * abs(avg_p - avg_y)
    return total / len(ps)


def auc(ps: list[float], ys: list[int]) -> float:
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    pos = sum(ys)
    neg = len(ys) - pos
    if pos == 0 or neg == 0:
        return 0.5
    rs = sum(k + 1 for k, i in enumerate(order) if ys[i])
    return (rs - pos * (pos + 1) / 2) / (pos * neg)


def main() -> None:
    rng = random.Random(29)
    wc = [rng.uniform(-0.5, 0.5) for _ in range(8)]
    n = 20000
    xs = [[rng.gauss(0, 1) for _ in range(8)] for _ in range(n)]
    ys = [1 if rng.random() < sigmoid(sum(wc[i] * x[i] for i in range(8)) - 2.0) else 0 for x in xs]

    tr = range(16000)
    te = range(16000, n)
    pos = [i for i in tr if ys[i]]
    neg = [i for i in tr if not ys[i]]
    rng.shuffle(neg)
    keep = neg[: len(neg) // 10]  # keep 10% of negatives

    w_full = fit([xs[i] for i in tr], [ys[i] for i in tr])
    ds = sorted(pos + keep)
    w_down = fit([xs[i] for i in ds], [ys[i] for i in ds])

    ps_full = [predict(w_full, xs[i]) for i in te]
    ps_down = [predict(w_down, xs[i]) for i in te]
    r = len(keep) / len(neg)  # sampling ratio
    ps_corr = [q * r / (1.0 - q + q * r) for q in ps_down]
    ys_te = [ys[i] for i in te]

    print("negative sampling, read (10x downsample, then correct):")
    print(f"  {'model':<18}{'auc':>7}{'ece':>8}")
    print(f"  {'full set':<18}{auc(ps_full, ys_te):>7.3f}{ece(ps_full, ys_te):>8.3f}")
    print(f"  {'downsampled':<18}{auc(ps_down, ys_te):>7.3f}{ece(ps_down, ys_te):>8.3f}")
    print(f"  {'downsampled+corrected':<18}{auc(ps_corr, ys_te):>7.3f}{ece(ps_corr, ys_te):>8.3f}")
    print()
    print("reading: downsampling costs almost no ranking (auc holds) while")
    print("breaking calibration: the base rate inside the model is 10x the")
    print("true one, so every probability inflates. the ratio correction")
    print("pulls the probabilities back to the true scale; ranking metrics")
    print("alone would never have caught the break.")


if __name__ == "__main__":
    main()
