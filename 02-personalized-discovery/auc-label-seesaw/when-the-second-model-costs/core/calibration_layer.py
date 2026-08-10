"""When the second model costs: ranking separates scores without
preserving their meaning, so the click head's probability drifts from the
rate (stage 64's audit measured slope 1.188). A calibration layer --
temperature scaling here -- re-maps the score to the rate, but it is a
second model with its own freshness: fit once on a calibration split, it
goes stale when the traffic distribution shifts, and the pCTR consumers
downstream read the stale mapping. This read fits T on one split and
measures what a distribution shift does to a frozen T.

Run:
    uv run python core/calibration_layer.py
"""

from __future__ import annotations

import math
import random


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-min(max(z, -30.0), 30.0)))


def bce(y: int, p: float) -> float:
    p = min(max(p, 1e-12), 1.0 - 1e-12)
    return -y * math.log(p) - (1.0 - y) * math.log(1.0 - p)


def fit(xs: list[list[float]], ys: list[int], epochs: int = 60, lr: float = 0.3) -> list[float]:
    w = [0.0] * 9
    n = len(xs)
    for _ in range(epochs):
        g = [0.0] * 9
        for x, y in zip(xs, ys):
            p = sigmoid(sum(w[i] * x[i] for i in range(8)) + w[8])
            e = p - y
            for i in range(8):
                g[i] += e * x[i]
            g[8] += e
        for i in range(9):
            w[i] -= lr * g[i] / n
    return w


def best_t(logits: list[float], ys: list[int]) -> float:
    """One-parameter temperature fit by grid search over T."""
    best, best_loss = 1.0, float("inf")
    for t in [i / 20 for i in range(5, 61)]:
        loss = sum(bce(y, sigmoid(z / t)) for z, y in zip(logits, ys))
        if loss < best_loss:
            best, best_loss = t, loss
    return best


def slope_intercept(ps: list[float], ys: list[int], bins: int = 10) -> tuple[float, float]:
    pairs = sorted(zip(ps, ys))
    rows = []
    for b in range(bins):
        chunk = pairs[b * len(pairs) // bins : (b + 1) * len(pairs) // bins]
        rows.append((sum(p for p, _ in chunk) / len(chunk),
                     sum(y for _, y in chunk) / len(chunk)))
    mx = sum(p for p, _ in rows) / bins
    my = sum(r for _, r in rows) / bins
    cov = sum((p - mx) * (r - my) for p, r in rows)
    var = sum((p - mx) ** 2 for p, _ in rows)
    return cov / var, my - (cov / var) * mx


def main() -> None:
    rng = random.Random(11)
    n = 4800
    xs = [[rng.gauss(0, 1) for _ in range(8)] for _ in range(n)]
    w = [0.9, 0.3, 0.6, -0.2, 0.1, 0.0, 0.0, 0.0]
    ys = [1 if rng.random() < sigmoid(sum(w[i] * x[i] for i in range(8)) - 0.3)
          else 0 for x in xs]
    fit_w = fit(xs[:3600], ys[:3600])
    logits = [sum(fit_w[i] * x[i] for i in range(8)) + fit_w[8] for x in xs[3600:]]
    ps = [sigmoid(z) for z in logits]
    ys_val = ys[3600:]
    t = best_t(logits, ys_val)
    scaled = [sigmoid(z / t) for z in logits]
    s0, i0 = slope_intercept(ps, ys_val)
    s1, i1 = slope_intercept(scaled, ys_val)

    shifted_logits = [z + 0.45 for z in logits]
    ps_shift = [sigmoid(z) for z in shifted_logits]
    scaled_stale = [sigmoid(z / t) for z in shifted_logits]
    s2, i2 = slope_intercept(ps_shift, ys_val)
    s3, i3 = slope_intercept(scaled_stale, ys_val)

    print("when the second model costs, read (temperature scaling):")
    print(f"  fitted T: {t:.2f}")
    print(f"  {'read':<28}{'slope':>7}{'intercept':>10}")
    print(f"  {'raw scores':<28}{s0:>7.3f}{i0:>10.3f}")
    print(f"  {'temperature-scaled':<28}{s1:>7.3f}{i1:>10.3f}")
    print(f"  {'shifted, raw':<28}{s2:>7.3f}{i2:>10.3f}")
    print(f"  {'shifted, stale T':<28}{s3:>7.3f}{i3:>10.3f}")
    print()
    print("reading: the raw ranking score is not a probability (slope off")
    print("1.0), and temperature scaling repairs the mapping on the split")
    print("it was fitted on. the layer is a second model with its own")
    print("freshness: a distribution shift breaks the frozen T, so the")
    print("calibration must be re-fitted or monitored, and the cost is")
    print("operational -- a monitoring job, a re-fit cadence, and a")
    print("handoff to every pCTR consumer.")


if __name__ == "__main__":
    main()
