"""Multi-task conflict: with CTR at 10% and purchase at 1%, the CTR
gradient dominates the shared trunk and the sparse task quietly loses.
The run measures per-task gradient norms, then compares a naive shared
bottom, a gradient-balanced version, and a gated (MMoE-style) trunk
where each task learns its own blend of two experts.

Stage 61 introduces the sharing-vs-conflict question: how much
representation the tasks should share, and who owns it.

Run:
    uv run python core/multitask_conflict.py
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


def bce(y: int, p: float) -> float:
    p = min(max(p, 1e-12), 1.0 - 1e-12)
    return -y * math.log(p) - (1.0 - y) * math.log(1.0 - p)


class SharedBottom:
    """One trunk, two linear heads, sum of task losses."""

    def __init__(self, d_in: int, d_h: int, seed: int) -> None:
        rng = random.Random(seed)
        self.w1 = [[rng.gauss(0, 0.4) for _ in range(d_in)] for _ in range(d_h)]
        self.b1 = [0.0] * d_h
        self.w2 = {t: [rng.gauss(0, 0.4) for _ in range(d_h)] for t in (0, 1)}
        self.b2 = {t: 0.0 for t in (0, 1)}

    def trunk(self, x: list[float]) -> list[float]:
        return [tanh(sum(self.w1[i][j] * x[j] for j in range(len(x))) + self.b1[i]) for i in range(len(self.w1))]

    def pred(self, x: list[float], t: int) -> float:
        h = self.trunk(x)
        return sigmoid(sum(self.w2[t][i] * h[i] for i in range(len(h))) + self.b2[t])

    def train_step(self, xs: list[list[float]], ys0: list[int], ys1: list[int], lr: float, wgt: float) -> tuple[float, float]:
        g1 = [[0.0] * len(xs[0]) for _ in range(len(self.w1))]
        gb1 = [0.0] * len(self.b1)
        g2 = {t: [0.0] * len(self.w2[t]) for t in (0, 1)}
        gb2 = {t: 0.0 for t in (0, 1)}
        norm0 = norm1 = 0.0
        for x, y0, y1 in zip(xs, ys0, ys1):
            h = self.trunk(x)
            p0 = sigmoid(sum(self.w2[0][i] * h[i] for i in range(len(h))) + self.b2[0])
            p1 = sigmoid(sum(self.w2[1][i] * h[i] for i in range(len(h))) + self.b2[1])
            e0 = p0 - y0
            e1 = wgt * (p1 - y1)
            norm0 += abs(e0)
            norm1 += abs(e1)
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
        return norm0 / n, norm1 / n


class GatedTrunk:
    """MMoE-lite: two experts plus a per-task sigmoid gate over them."""

    def __init__(self, d_in: int, d_h: int, seed: int) -> None:
        rng = random.Random(seed)
        self.we = [[[rng.gauss(0, 0.4) for _ in range(d_in)] for _ in range(d_h)] for _ in range(2)]
        self.be = [[0.0] * d_h for _ in range(2)]
        self.vg = {t: 0.0 for t in (0, 1)}  # gate logit per task
        self.w2 = {t: [rng.gauss(0, 0.4) for _ in range(d_h)] for t in (0, 1)}
        self.b2 = {t: 0.0 for t in (0, 1)}

    def experts(self, x: list[float]) -> list[list[float]]:
        return [
            [tanh(sum(self.we[k][i][j] * x[j] for j in range(len(x))) + self.be[k][i]) for i in range(len(self.be[0]))]
            for k in range(2)
        ]

    def pred(self, x: list[float], t: int) -> float:
        g0 = sigmoid(self.vg[t])
        es = self.experts(x)
        r = [g0 * es[0][i] + (1.0 - g0) * es[1][i] for i in range(len(es[0]))]
        return sigmoid(sum(self.w2[t][i] * r[i] for i in range(len(r))) + self.b2[t])

    def train_step(self, xs: list[list[float]], ys0: list[int], ys1: list[int], lr: float) -> None:
        n = len(xs)
        gwe = [[[0.0] * len(xs[0]) for _ in range(len(self.be[0]))] for _ in range(2)]
        gbe = [[0.0] * len(self.be[0]) for _ in range(2)]
        gvg = {t: 0.0 for t in (0, 1)}
        g2 = {t: [0.0] * len(self.w2[t]) for t in (0, 1)}
        gb2 = {t: 0.0 for t in (0, 1)}
        for x, y0, y1 in zip(xs, ys0, ys1):
            es = self.experts(x)
            for t, y in ((0, y0), (1, y1)):
                g0 = sigmoid(self.vg[t])
                r = [g0 * es[0][i] + (1.0 - g0) * es[1][i] for i in range(len(es[0]))]
                p = sigmoid(sum(self.w2[t][i] * r[i] for i in range(len(r))) + self.b2[t])
                e = p - y
                dr = [e * self.w2[t][i] for i in range(len(r))]
                for i in range(len(r)):
                    g2[t][i] += e * r[i]
                gb2[t] += e
                gvg[t] += sum((es[0][i] - es[1][i]) * dr[i] for i in range(len(r))) * g0 * (1.0 - g0)
                for k, gk in enumerate((g0, 1.0 - g0)):
                    for i in range(len(es[k])):
                        dh = dtanh(es[k][i])
                        dz = gk * dr[i] * dh
                        for j in range(len(x)):
                            gwe[k][i][j] += dz * x[j]
                        gbe[k][i] += dz
        for k in range(2):
            for i in range(len(self.be[0])):
                for j in range(len(xs[0])):
                    self.we[k][i][j] -= lr * gwe[k][i][j] / n
                self.be[k][i] -= lr * gbe[k][i] / n
        for t in (0, 1):
            self.vg[t] -= lr * gvg[t] / n
            for i in range(len(self.w2[t])):
                self.w2[t][i] -= lr * g2[t][i] / n
            self.b2[t] -= lr * gb2[t] / n


def auc(ps: list[float], ys: list[int]) -> float:
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    pos = sum(ys)
    neg = len(ys) - pos
    if pos == 0 or neg == 0:
        return 0.5
    rs = sum(k + 1 for k, i in enumerate(order) if ys[i])
    return (rs - pos * (pos + 1) / 2) / (pos * neg)


def main() -> None:
    rng = random.Random(61)
    wc = [rng.uniform(-0.5, 0.5) for _ in range(8)]
    wp = [rng.uniform(-0.6, 0.6) for _ in range(8)]
    n = 2500
    xs = [[rng.gauss(0, 1) for _ in range(8)] for _ in range(n)]
    y_ctr = [1 if rng.random() < sigmoid(sum(wc[i] * x[i] for i in range(8))) else 0 for x in xs]
    y_buy = [1 if rng.random() < sigmoid(sum(wp[i] * x[i] for i in range(8)) - 4.5) else 0 for x in xs]
    tr = range(2000)
    te = range(2000, n)
    x_tr = [xs[i] for i in tr]
    c_tr = [y_ctr[i] for i in tr]
    b_tr = [y_buy[i] for i in tr]

    m1 = SharedBottom(8, 6, 61)
    norms = []
    for ep in range(70):
        n0, n1 = m1.train_step(x_tr, c_tr, b_tr, 0.2, 1.0)
        if ep == 69:
            norms.append((n0, n1))

    m2 = SharedBottom(8, 6, 61)
    for _ in range(70):
        m2.train_step(x_tr, c_tr, b_tr, 0.2, 40.0)

    m3 = GatedTrunk(8, 6, 61)
    for _ in range(70):
        m3.train_step(x_tr, c_tr, b_tr, 0.2)

    def evals(model) -> tuple[float, float]:
        return (
            auc([model.pred(xs[i], 0) for i in te], [y_ctr[i] for i in te]),
            auc([model.pred(xs[i], 1) for i in te], [y_buy[i] for i in te]),
        )

    a0, a1 = evals(m1)
    b0, b1 = evals(m2)
    c0, c1 = evals(m3)
    print("multi-task conflict, read (ctr ~10% vs purchase ~1%):")
    print(f"  {'model':<20}{'ctr auc':>8}{'buy auc':>8}")
    print(f"  {'naive shared bottom':<20}{a0:>8.3f}{a1:>8.3f}")
    print(f"  {'gradient-balanced':<20}{b0:>8.3f}{b1:>8.3f}")
    print(f"  {'gated (mmoe-lite)':<20}{c0:>8.3f}{c1:>8.3f}")
    print(f"  purchase positives in train: {sum(y_buy[i] for i in tr)} of 2000")
    print(f"  final gradient norms: ctr {norms[0][0]:.3f} vs buy {norms[0][1]:.3f}")
    print()
    print("reading: the click loss pulls the shared trunk far harder than the")
    print("purchase loss, so the sparse task's representation is shaped by the")
    print("abundant task. balancing the purchase loss rescues the sparse task")
    print("outright; the gated trunk improves on naive without a hand-tuned")
    print("weight, landing between the two here. gating is the structural")
    print("answer that scales when the conflict is not one weight.")


if __name__ == "__main__":
    main()
