"""Sparse labels: the objective's labels are rare, empty, or slow. With
cold users and cold items, whole slices of the exposure space have almost
no purchase labels, and a model trained only where the labels exist
never learns to rank the slices it cannot measure. The dense click task
shares features with the sparse buy task, so a multi-task trunk can
borrow the dense representation; a surrogate label (engaged-as-purchase)
adds positives but imports noise.

The run generates a cohort with a head slice, a cold-user slice, and a
cold-item slice, labels purchases with a delay, and trains three
variants: a buy-only model on the cold rows (starved), a shared
multi-task trunk (borrows the click representation), and a surrogate
label variant. It then reports the per-slice AUCs and, with --emit-log,
writes the envelope for the density audit.

Stage 65 introduces the label-health question: what the density report
by slice shows, and which fix layer each diagnosis points to.

Run:
    uv run python core/sparse_labels.py
    uv run python core/sparse_labels.py --emit-log /tmp/sparse-envelope.json
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-min(max(z, -30.0), 30.0)))


def tanh(z: float) -> float:
    return math.tanh(z)


def dtanh(t: float) -> float:
    return 1.0 - t * t


def lognormal(rng: random.Random, median: float, sigma: float) -> float:
    return math.exp(math.log(median) + sigma * rng.gauss(0, 1))


def auc(ps: list[float], ys: list[int]) -> float:
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    pos = sum(ys)
    neg = len(ys) - pos
    if pos == 0 or neg == 0:
        return 0.5
    rs = sum(k + 1 for k, i in enumerate(order) if ys[i])
    return (rs - pos * (pos + 1) / 2) / (pos * neg)


class SparseNet:
    """Two-head net: a click head over all rows and a buy head over all
    rows, so the sparse task reads a trunk shaped by the dense task."""

    def __init__(self, d_in: int, d_h: int, seed: int) -> None:
        rng = random.Random(seed)
        self.w1 = [[rng.gauss(0, 0.4) for _ in range(d_in)] for _ in range(d_h)]
        self.b1 = [0.0] * d_h
        self.w2 = {t: [rng.gauss(0, 0.4) for _ in range(d_h)] for t in (0, 1)}
        self.b2 = {t: 0.0 for t in (0, 1)}

    def trunk(self, x: list[float]) -> list[float]:
        return [
            tanh(sum(self.w1[i][j] * x[j] for j in range(len(x))) + self.b1[i])
            for i in range(len(self.w1))
        ]

    def pred(self, x: list[float], t: int) -> float:
        h = self.trunk(x)
        return sigmoid(sum(self.w2[t][i] * h[i] for i in range(len(h))) + self.b2[t])

    def train_step(
        self,
        xs: list[list[float]],
        ys0: list[int],
        ys1: list[int],
        lr: float,
        buy_wgt: float = 1.0,
    ) -> None:
        g1 = [[0.0] * len(xs[0]) for _ in range(len(self.w1))]
        gb1 = [0.0] * len(self.b1)
        g2 = {t: [0.0] * len(self.w2[t]) for t in (0, 1)}
        gb2 = {t: 0.0 for t in (0, 1)}
        for x, y0, y1 in zip(xs, ys0, ys1):
            h = self.trunk(x)
            p0 = sigmoid(sum(self.w2[0][i] * h[i] for i in range(len(h))) + self.b2[0])
            p1 = sigmoid(sum(self.w2[1][i] * h[i] for i in range(len(h))) + self.b2[1])
            e0 = p0 - y0
            e1 = buy_wgt * (p1 - y1)
            for i in range(len(h)):
                g2[0][i] += e0 * h[i]
                g2[1][i] += e1 * h[i]
            gb2[0] += e0
            gb2[1] += e1
            for i in range(len(h)):
                dh = dtanh(h[i])
                dz = (e0 * self.w2[0][i] + e1 * self.w2[1][i]) * dh
                for j in range(len(x)):
                    g1[i][j] += dz * x[j]
                gb1[i] += dz
        n = len(xs)
        for i in range(len(self.w1)):
            for j in range(len(self.w1[0])):
                self.w1[i][j] -= lr * g1[i][j] / n
            self.b1[i] -= lr * gb1[i] / n
        for t in (0, 1):
            for i in range(len(self.w2[t])):
                self.w2[t][i] -= lr * g2[t][i] / n
            self.b2[t] -= lr * gb2[t] / n


def logistic_fit(
    xs: list[list[float]],
    ys: list[int],
    epochs: int = 80,
    lr: float = 0.3,
) -> list[float]:
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


def generate(
    seed: int,
) -> tuple[list[list[float]], list[str], list[int], list[int], list[float], float]:
    """Cohort with three slices. Clicks depend on activity and item
    popularity; purchases depend on the same item features plus
    freshness, so the click trunk carries signal the buy task needs.
    Purchase labels arrive with a log-normal delay; the snapshot is young
    enough that a share of real purchases is still in flight."""
    rng = random.Random(seed)
    n = 8000
    xs, slices, y_click, y_buy, delay = [], [], [], [], []
    for _ in range(n):
        x0 = rng.gauss(0, 1)
        x = [x0, rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1),
             rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)]
        if x[2] < -1.0:
            slice_name = "cold-item"
        elif x0 >= 0:
            slice_name = "head"
        else:
            slice_name = "cold-user"
        if slice_name == "head":
            click_logit = 1.0 * x0 + 0.9 * x[2] + 0.2 * x[1] + 0.4 * x[3] - 0.4
        elif slice_name == "cold-user":
            click_logit = 0.3 * x0 + 0.9 * x[2] + 0.5 * x[1] + 0.4 * x[3] - 1.0
        else:
            click_logit = 0.2 * x0 + 1.1 * x[2] + 0.2 * x[1] + 0.4 * x[3] - 1.2
        adj = 0.3 if slice_name == "head" else (-0.8 if slice_name == "cold-item" else -0.3)
        buy_logit = 0.9 * x[2] + 0.4 * x[3] + adj - 3.9
        xs.append(x)
        slices.append(slice_name)
        y_click.append(1 if rng.random() < sigmoid(click_logit) else 0)
        buys = 1 if rng.random() < sigmoid(buy_logit) else 0
        y_buy.append(buys)
        delay.append(lognormal(rng, 0.4, 0.5) if buys else 0.0)
    snapshot = 0.6
    return xs, slices, y_click, y_buy, delay, snapshot


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit-log", default=None)
    args = parser.parse_args(argv)

    xs, slices, y_click, y_buy, delay, snapshot = generate(42)
    n = len(xs)
    tr = range(6400)
    te = list(range(6400, n))
    x_tr = [xs[i] for i in tr]
    c_tr = [y_click[i] for i in tr]
    b_tr = [y_buy[i] for i in tr]

    cold = [i for i in tr if slices[i] != "head"]
    x_cold = [xs[i] for i in cold]
    b_cold = [y_buy[i] for i in cold]

    cold_only = logistic_fit(x_cold, b_cold)
    shared = SparseNet(8, 6, 61)
    for _ in range(70):
        shared.train_step(x_tr, c_tr, b_tr, 0.2, buy_wgt=10.0)

    surrogate_buy = list(b_tr)
    for i in cold:
        engaged = 1 if y_click[i] and xs[i][3] > 0 else 0
        surrogate_buy[i] = engaged
    surrogate = SparseNet(8, 6, 61)
    for _ in range(70):
        surrogate.train_step(x_tr, c_tr, surrogate_buy, 0.2, buy_wgt=10.0)

    def tail_buy_auc(model) -> float:
        return auc(
            [model.pred(xs[i], 1) for i in te if slices[i] != "head"],
            [y_buy[i] for i in te if slices[i] != "head"],
        )

    def cold_only_pred(i: int) -> float:
        x = xs[i]
        return sigmoid(sum(cold_only[j] * x[j] for j in range(8)) + cold_only[8])

    a = auc([cold_only_pred(i) for i in te if slices[i] != "head"],
            [y_buy[i] for i in te if slices[i] != "head"])
    b = tail_buy_auc(shared)
    c = tail_buy_auc(surrogate)

    print("sparse labels, read (buy over cold slices):")
    print(f"  {'variant':<24}{'cold-slice buy auc':>19}")
    print(f"  {'cold-only, from scratch':<24}{a:>19.3f}")
    print(f"  {'shared trunk (click+buy)':<24}{b:>19.3f}")
    print(f"  {'surrogate (engaged)':<24}{c:>19.3f}")
    print(f"  buy positives in train: head {sum(y_buy[i] for i in tr if slices[i] == 'head')}, "
          f"cold-user {sum(y_buy[i] for i in tr if slices[i] == 'cold-user')}, "
          f"cold-item {sum(y_buy[i] for i in tr if slices[i] == 'cold-item')}")
    print(f"  in-flight purchases at snapshot {snapshot}d: "
          f"{sum(1 for d in delay[:6400] if d > snapshot)}")
    print()
    print("reading: a buy-only model trained where the labels exist is")
    print("starved on the cold-item slice -- five train positives cannot")
    print("shape a ranker, and the cold-only model is really a cold-user")
    print("model. the shared trunk borrows the click representation only")
    print("when the buy loss is balanced (stage 61); the surrogate label")
    print("fills the empty slice with positives at the cost of importing")
    print("the surrogate's noise into every predicted probability.")

    if args.emit_log:
        envelope = {
            "snapshot": snapshot,
            "rows": [
                {
                    "slice": slices[i],
                    "click": y_click[i],
                    "buy": y_buy[i],
                    "delay": delay[i],
                    "shared_click": shared.pred(xs[i], 0),
                    "shared_buy": shared.pred(xs[i], 1),
                    "surrogate_buy": surrogate.pred(xs[i], 1),
                }
                for i in te
            ]
        }
        with open(args.emit_log, "w") as fh:
            json.dump(envelope, fh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
