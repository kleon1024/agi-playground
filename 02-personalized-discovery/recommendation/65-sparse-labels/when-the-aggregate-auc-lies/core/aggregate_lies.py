"""When the aggregate AUC lies: the stage audit showed a cold-item slice
whose 5-95% interval spans chance while the aggregate number looks fine.
This read turns that into arithmetic: how many positives does a slice
need before its AUC interval stops spanning chance, measured by
subsampling the dense head slice. The answer is the guardrail -- you
cannot shrink the interval by modeling alone; you need labels, which is
a data decision, not a model decision.

Run:
    uv run python core/aggregate_lies.py
"""

from __future__ import annotations

import math
import random


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-min(max(z, -30.0), 30.0)))


def tanh(z: float) -> float:
    return math.tanh(z)


def dtanh(t: float) -> float:
    return 1.0 - t * t


def auc(ps: list[float], ys: list[int]) -> float:
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    pos = sum(ys)
    neg = len(ys) - pos
    if pos == 0 or neg == 0:
        return 0.5
    rs = sum(k + 1 for k, i in enumerate(order) if ys[i])
    return (rs - pos * (pos + 1) / 2) / (pos * neg)


class Net:
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

    def train_step(self, xs, ys0, ys1, lr, buy_wgt=1.0) -> None:
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


def generate(seed: int) -> tuple[list[list[float]], list[str], list[int], list[int]]:
    rng = random.Random(seed)
    n = 8000
    xs, slices, y_click, y_buy = [], [], [], []
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
        y_buy.append(1 if rng.random() < sigmoid(buy_logit) else 0)
    return xs, slices, y_click, y_buy


def main() -> None:
    xs, slices, y_click, y_buy = generate(42)
    tr = range(6400)
    te = list(range(6400, 8000))
    x_tr = [xs[i] for i in tr]
    c_tr = [y_click[i] for i in tr]
    b_tr = [y_buy[i] for i in tr]
    net = Net(8, 6, 61)
    for _ in range(70):
        net.train_step(x_tr, c_tr, b_tr, 0.2, buy_wgt=10.0)

    head_te = [i for i in te if slices[i] == "head"]
    ps = [net.pred(xs[i], 1) for i in head_te]
    ys = [y_buy[i] for i in head_te]
    print("when the aggregate AUC lies, read (bootstrap interval):")
    print(f"  {'positives':<10}{'10-90 pct interval':>24}")
    rng = random.Random(0)
    for k in (2, 5, 10, 20, 30):
        aucs = []
        for _ in range(120):
            idx = rng.sample(range(len(ps)), k)
            sub_p = [ps[i] for i in idx]
            sub_y = [ys[i] for i in idx]
            order = sorted(range(k), key=lambda i: sub_p[i])
            pos = sum(sub_y)
            if pos == 0 or pos == k:
                continue
            rs = sum(j + 1 for j, i in enumerate(order) if sub_y[i])
            a = (rs - pos * (pos + 1) / 2) / (pos * (k - pos))
            aucs.append(a)
        if aucs:
            aucs.sort()
            lo = aucs[int(0.1 * (len(aucs) - 1))]
            hi = aucs[int(0.9 * (len(aucs) - 1))]
            print(f"  {k:<10}{f'{lo:.3f} .. {hi:.3f} (w={hi - lo:.3f})':>24}")
    print()
    print("reading: with two positives the interval is so wide it spans")
    print("chance -- no modeling choice changes that, only the label")
    print("supply does. the aggregate number is not lying, it is just")
    print("measured where the labels are. the guardrail for a sparse")
    print("slice is a data decision: longer window, surrogate labels,")
    print("or exposure data, gated on the slice's interval, not the")
    print("aggregate AUC.")


if __name__ == "__main__":
    main()
