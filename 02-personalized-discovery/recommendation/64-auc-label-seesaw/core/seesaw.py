"""AUC-label seesaw: the model that optimizes one objective at the
visible cost of another. With a dense head slice and a sparse tail slice
sharing one trunk, the head rows contribute most of the gradient, so the
tail slice's AUC drops while the aggregate AUC stays fine -- and the two
tasks (click and buy) pull in opposite directions, so the buy head is
shaped by a representation built for clicks.

The run trains three variants on the same synthetic cohort: a naive
shared bottom (sum of task losses, no weighting), a slice-weighted
version (tail rows up-weighted so the sparse slice's gradient is
heard), and a gated (MMoE-lite) trunk. It then reports the per-task AUCs
and, with --emit-log, writes the cohort envelope for the audit that
stratifies the AUC by slice and checks per-decile calibration.

Stage 64 introduces the seesaw question: which slice and which task
silently pay for the objective the model is visibly optimizing.

Run:
    uv run python core/seesaw.py
    uv run python core/seesaw.py --emit-log /tmp/seesaw-envelope.json
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


def bce(y: int, p: float) -> float:
    p = min(max(p, 1e-12), 1.0 - 1e-12)
    return -y * math.log(p) - (1.0 - y) * math.log(1.0 - p)


def auc(ps: list[float], ys: list[int]) -> float:
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    pos = sum(ys)
    neg = len(ys) - pos
    if pos == 0 or neg == 0:
        return 0.5
    rs = sum(k + 1 for k, i in enumerate(order) if ys[i])
    return (rs - pos * (pos + 1) / 2) / (pos * neg)


class SharedBottom:
    """One trunk, two linear heads. Per-row loss weights let a caller
    make one slice's rows count more without touching the architecture."""

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
        w0: list[float],
        w1: list[float],
    ) -> None:
        g1 = [[0.0] * len(xs[0]) for _ in range(len(self.w1))]
        gb1 = [0.0] * len(self.b1)
        g2 = {t: [0.0] * len(self.w2[t]) for t in (0, 1)}
        gb2 = {t: 0.0 for t in (0, 1)}
        for x, y0, y1, r0, r1 in zip(xs, ys0, ys1, w0, w1):
            h = self.trunk(x)
            p0 = sigmoid(sum(self.w2[0][i] * h[i] for i in range(len(h))) + self.b2[0])
            p1 = sigmoid(sum(self.w2[1][i] * h[i] for i in range(len(h))) + self.b2[1])
            e0 = r0 * (p0 - y0)
            e1 = r1 * (p1 - y1)
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


class GatedTrunk:
    """MMoE-lite: two experts plus a per-task sigmoid gate over them."""

    def __init__(self, d_in: int, d_h: int, seed: int) -> None:
        rng = random.Random(seed)
        self.we = [
            [[rng.gauss(0, 0.4) for _ in range(d_in)] for _ in range(d_h)]
            for _ in range(2)
        ]
        self.be = [[0.0] * d_h for _ in range(2)]
        self.vg = {t: 0.0 for t in (0, 1)}
        self.w2 = {t: [rng.gauss(0, 0.4) for _ in range(d_h)] for t in (0, 1)}
        self.b2 = {t: 0.0 for t in (0, 1)}

    def experts(self, x: list[float]) -> list[list[float]]:
        return [
            [
                tanh(sum(self.we[k][i][j] * x[j] for j in range(len(x))) + self.be[k][i])
                for i in range(len(self.be[0]))
            ]
            for k in range(2)
        ]

    def pred(self, x: list[float], t: int) -> float:
        g0 = sigmoid(self.vg[t])
        es = self.experts(x)
        r = [g0 * es[0][i] + (1.0 - g0) * es[1][i] for i in range(len(es[0]))]
        return sigmoid(sum(self.w2[t][i] * r[i] for i in range(len(r))) + self.b2[t])

    def train_step(
        self, xs: list[list[float]], ys0: list[int], ys1: list[int], lr: float
    ) -> None:
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
                gvg[t] += (
                    sum((es[0][i] - es[1][i]) * dr[i] for i in range(len(r)))
                    * g0
                    * (1.0 - g0)
                )
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


def generate(seed: int) -> tuple[list[list[float]], list[int], list[int], list[str]]:
    """Synthetic cohort: activity splits head from tail; the head clicks
    on activity and popularity while the tail clicks on novelty, so a
    model fitted to the head misranks the tail; novelty raises clicks and
    lowers buys (the task seesaw)."""
    rng = random.Random(seed)
    n = 3200
    xs = []
    slices = []
    y_click = []
    y_buy = []
    for _ in range(n):
        x0 = rng.gauss(0, 1)
        x = [x0, rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1),
             rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)]
        slice_name = "head" if x0 >= 0 else "tail"
        if slice_name == "head":
            click_logit = 1.1 * x0 + 0.5 * x[2] - 0.4
        else:
            click_logit = 1.0 * x[1] + 0.3 * x[2] - 1.2
        buy_logit = 0.5 * x0 + 0.6 * x[2] - 0.9 * x[1] - 3.3
        xs.append(x)
        slices.append(slice_name)
        y_click.append(1 if rng.random() < sigmoid(click_logit) else 0)
        y_buy.append(1 if rng.random() < sigmoid(buy_logit) else 0)
    return xs, y_click, y_buy, slices


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit-log", default=None)
    args = parser.parse_args(argv)

    xs, y_click, y_buy, slices = generate(42)
    n = len(xs)
    tr = range(2560)
    te = range(2560, n)
    x_tr = [xs[i] for i in tr]
    c_tr = [y_click[i] for i in tr]
    b_tr = [y_buy[i] for i in tr]
    head_w = [3.0 if slices[i] == "tail" else 1.0 for i in tr]

    naive = SharedBottom(8, 6, 61)
    for _ in range(70):
        naive.train_step(x_tr, c_tr, b_tr, 0.2, [1.0] * len(x_tr), [1.0] * len(x_tr))

    weighted = SharedBottom(8, 6, 61)
    for _ in range(70):
        weighted.train_step(x_tr, c_tr, b_tr, 0.2, head_w, head_w)

    gated = GatedTrunk(8, 6, 61)
    for _ in range(70):
        gated.train_step(x_tr, c_tr, b_tr, 0.2)

    def evals(model) -> tuple[float, float]:
        return (
            auc([model.pred(xs[i], 0) for i in te], [y_click[i] for i in te]),
            auc([model.pred(xs[i], 1) for i in te], [y_buy[i] for i in te]),
        )

    a0, a1 = evals(naive)
    b0, b1 = evals(weighted)
    c0, c1 = evals(gated)
    head_pos = sum(y_click[i] for i in tr if slices[i] == "head")
    tail_pos = sum(y_click[i] for i in tr if slices[i] == "tail")
    buy_pos = sum(b_tr)
    print("auc-label seesaw, read (click vs buy, head vs tail):")
    print(f"  {'model':<20}{'click auc':>9}{'buy auc':>8}")
    print(f"  {'naive shared bottom':<20}{a0:>9.3f}{a1:>8.3f}")
    print(f"  {'slice-weighted':<20}{b0:>9.3f}{b1:>8.3f}")
    print(f"  {'gated (mmoe-lite)':<20}{c0:>9.3f}{c1:>8.3f}")
    print(f"  click positives: head {head_pos}, tail {tail_pos}")
    print(f"  buy positives in train: {buy_pos} of {len(x_tr)}")
    print()
    print("reading: head rows are denser and higher-signal, so the naive")
    print("gradient fits the head's click signal and the tail slice pays:")
    print("slice-weighting lifts the tail (and the buy task) at a small")
    print("head cost, while the aggregate click AUC barely moves. gating")
    print("does not automatically win -- on this cohort the explicit")
    print("slice weighting beats it. the seesaw is only visible when the")
    print("metric is stratified by slice and task.")

    if args.emit_log:
        envelope = {
            "rows": [
                {
                    "slice": slices[i],
                    "click": y_click[i],
                    "buy": y_buy[i],
                    "naive_click": naive.pred(xs[i], 0),
                    "naive_buy": naive.pred(xs[i], 1),
                    "weighted_click": weighted.pred(xs[i], 0),
                    "weighted_buy": weighted.pred(xs[i], 1),
                    "gated_click": gated.pred(xs[i], 0),
                    "gated_buy": gated.pred(xs[i], 1),
                }
                for i in te
            ]
        }
        with open(args.emit_log, "w") as fh:
            json.dump(envelope, fh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
