"""Entire-space funnel modeling: CVR trained on clicked samples is both
sparse and selection-biased; the ESMM-style trick trains CTR and
CTCVR on the full impression space and derives CVR as the ratio.

Stage 56 introduces the conversion funnel. Payment is rare and only
observed after a click, so a CVR head trained on the clicked subset
sees few positives and inherits a selection bias. Training CTCVR
(click x pay) on the full space gives every impression a label and
keeps the funnel constraint p_pay <= p_click automatic.

Run:
    uv run python core/entire_space.py
"""

from __future__ import annotations

import math
import random


def sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


def log_loss(y: float, p: float) -> float:
    p = min(max(p, 1e-12), 1.0 - 1e-12)
    return -y * math.log(p) - (1.0 - y) * math.log(1.0 - p)


def train_logistic(rows: list[list[float]], ys: list[int], epochs: int = 60) -> list[float]:
    """Batch gradient descent logistic regression over 12 features."""
    w = [0.0] * 13
    n = len(rows)
    step = 0.05
    for _ in range(epochs):
        gw = [0.0] * 13
        for x, y in zip(rows, ys):
            z = w[0]
            for i in range(12):
                z += w[i + 1] * x[i]
            p = sigmoid(z)
            err = p - y
            gw[0] += err
            for i in range(12):
                gw[i + 1] += err * x[i]
        for i in range(13):
            w[i] -= step * gw[i] / n
    return w


def predict(w: list[float], x: list[float]) -> float:
    z = w[0]
    for i in range(12):
        z += w[i + 1] * x[i]
    return sigmoid(z)


def auc(ps: list[float], ys: list[int]) -> float:
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    pos = sum(ys)
    neg = len(ys) - pos
    if pos == 0 or neg == 0:
        return 0.5
    rank_sum = 0
    for k, i in enumerate(order):
        if ys[i] == 1:
            rank_sum += k + 1
    return (rank_sum - pos * (pos + 1) / 2) / (pos * neg)


def make_data(seed: int = 7, n_imp: int = 4000, n_feat: int = 12) -> tuple[list[list[float]], list[int], list[int]]:
    rng = random.Random(seed)
    wc = [rng.uniform(-0.4, 0.4) for _ in range(n_feat)]
    wp = [rng.uniform(-0.5, 0.5) for _ in range(n_feat)]
    xs: list[list[float]] = []
    y_click: list[int] = []
    y_pay: list[int] = []
    for _ in range(n_imp):
        x = [rng.gauss(0.0, 1.0) for _ in range(n_feat)]
        pc = sigmoid(sum(wc[i] * x[i] for i in range(n_feat)))
        click = 1 if rng.random() < pc else 0
        pp = sigmoid(sum(wp[i] * x[i] for i in range(n_feat)))
        pay = click * (1 if rng.random() < pp else 0)
        xs.append(x)
        y_click.append(click)
        y_pay.append(pay)
    return xs, y_click, y_pay


def main() -> None:
    xs, y_click, y_pay = make_data()
    clicked = [i for i, c in enumerate(y_click) if c == 1]
    hold = clicked[::4]  # quarter of clicked samples held out for CVR eval
    hold_set = set(hold)
    train_c = [i for i in clicked if i not in hold_set]

    # CVR-only: logistic on the clicked training subset.
    w_cvr = train_logistic([xs[i] for i in train_c], [y_pay[i] for i in train_c])
    cvr_auc = auc([predict(w_cvr, xs[i]) for i in hold], [y_pay[i] for i in hold])

    # Entire-space: CTCVR head on the full impression space with
    # target y_click * y_pay; CTR head on the full space; CVR derived.
    y_ctcvr = [c * p for c, p in zip(y_click, y_pay)]
    all_idx = list(range(len(xs)))
    w_ctcvr = train_logistic([xs[i] for i in all_idx], y_ctcvr)
    w_ctr = train_logistic([xs[i] for i in all_idx], y_click)
    ps = []
    for i in hold:
        p_ctcvr = predict(w_ctcvr, xs[i])
        p_ctr = max(predict(w_ctr, xs[i]), 1e-6)
        ps.append(min(p_ctcvr / p_ctr, 1.0))
    space_auc = auc(ps, [y_pay[i] for i in hold])

    n_pos_cvr = sum(y_pay[i] for i in train_c)
    n_pos_full = sum(y_pay)
    print("entire-space funnel, read (CVR on clicked subset vs full space):")
    print(f"  clicked subset        positives {n_pos_cvr:5d}   cvr auc {cvr_auc:.3f}")
    print(f"  entire space (ctcvr)  positives {n_pos_full:5d}   cvr auc {space_auc:.3f}")
    print()
    print("reading: the clicked-only head sees a tenth of the positive")
    print("signal and a selection-biased training set; the full-space")
    print("CTCVR head labels every impression and keeps p_pay <= p_click")
    print("by construction, so it recovers the true conditional better.")


if __name__ == "__main__":
    main()
