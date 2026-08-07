"""When the surrogate label bleeds: filling an empty slice with proxy
labels gives the model something to rank, but the surrogate is not the
objective. Engaged-as-purchase imports a weaker signal into every
predicted probability: the model over-predicts true purchases on the
cold slice, and on the labels that actually matter its AUC is worse than
the shared model that kept the true labels. This read measures both the
rate inflation and the true-label AUC cost.

Run:
    uv run python core/surrogate_bleed.py
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
    surrogate_buy = list(b_tr)
    for i in range(6400):
        if slices[i] != "head":
            surrogate_buy[i] = 1 if y_click[i] and xs[i][3] > 0 else 0
    true_net = Net(8, 6, 61)
    for _ in range(70):
        true_net.train_step(x_tr, c_tr, b_tr, 0.2, buy_wgt=10.0)
    surr_net = Net(8, 6, 61)
    for _ in range(70):
        surr_net.train_step(x_tr, c_tr, surrogate_buy, 0.2, buy_wgt=10.0)

    cold_te = [i for i in te if slices[i] != "head"]
    a = auc([true_net.pred(xs[i], 1) for i in cold_te],
            [y_buy[i] for i in cold_te])
    b = auc([surr_net.pred(xs[i], 1) for i in cold_te],
            [y_buy[i] for i in cold_te])
    item_te = [i for i in te if slices[i] == "cold-item"]
    pred_mean = sum(surr_net.pred(xs[i], 1) for i in item_te) / len(item_te)
    true_rate = sum(y_buy[i] for i in item_te) / len(item_te)
    print("when the surrogate label bleeds, read (cold slices):")
    print(f"  {'model':<20}{'true-label buy auc':>18}")
    print(f"  {'true labels':<20}{a:>18.3f}")
    print(f"  {'surrogate labels':<20}{b:>18.3f}")
    print(f"  surrogate mean predicted buy rate on cold items: {pred_mean:.4f}")
    print(f"  true buy rate on cold items: {true_rate:.4f}")
    print()
    print("reading: the surrogate fills the empty slice -- engaged is")
    print("several times more frequent than purchase -- but the model")
    print("trained on it reads 'engaged' everywhere and over-predicts")
    print("purchase by the ratio above. on the labels that matter its")
    print("true-label AUC is the worse of the two. a surrogate buys")
    print("signal and sells probability meaning; the value tree (stage 05)")
    print("multiplies that inflated number into every downstream decision.")


if __name__ == "__main__":
    main()
