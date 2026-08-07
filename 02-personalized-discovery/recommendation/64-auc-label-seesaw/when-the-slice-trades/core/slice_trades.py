"""When the slice trades: the tail slice's AUC is bought with head AUC.
Stage 64's audit showed one point on the frontier (naive versus a fixed
3x tail weight). This read sweeps the tail weight and shows that the
frontier is a curve: the first weight steps buy the tail cheaply, then
the marginal tail gain shrinks while the head cost keeps growing. The
choice of where to sit is a product decision, not a model decision --
and the aggregate AUC is flat across the whole sweep, so it cannot tell
you where you are on the frontier.

Run:
    uv run python core/slice_trades.py
"""

from __future__ import annotations

import math
import random


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-min(max(z, -30.0), 30.0)))


def auc(ps: list[float], ys: list[int]) -> float:
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    pos = sum(ys)
    neg = len(ys) - pos
    if pos == 0 or neg == 0:
        return 0.5
    rs = sum(k + 1 for k, i in enumerate(order) if ys[i])
    return (rs - pos * (pos + 1) / 2) / (pos * neg)


def cohort(seed: int) -> tuple[list[list[float]], list[int], list[int], list[str]]:
    """Same generating structure as the stage: the head clicks on activity
    and popularity, the tail clicks on novelty, so a model fitted to the
    head misranks the tail."""
    rng = random.Random(seed)
    xs, slices, y_click, y_buy = [], [], [], []
    for _ in range(3200):
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


def fit_weighted(
    xs: list[list[float]],
    ys: list[int],
    slices: list[str],
    tail_w: float,
    epochs: int = 60,
    lr: float = 0.3,
) -> list[float]:
    w = [0.0] * 9
    n = len(xs)
    for _ in range(epochs):
        g = [0.0] * 9
        for k, (x, y) in enumerate(zip(xs, ys)):
            wgt = tail_w if slices[k] == "tail" else 1.0
            p = sigmoid(sum(w[i] * x[i] for i in range(8)) + w[8])
            e = (p - y) * wgt
            for i in range(8):
                g[i] += e * x[i]
            g[8] += e
        for i in range(9):
            w[i] -= lr * g[i] / n
    return w


def main() -> None:
    xs, y_click, _y_buy, slices = cohort(42)
    n = len(xs)
    tr = range(2560)
    te = list(range(2560, n))
    x_tr = [xs[i] for i in tr]
    c_tr = [y_click[i] for i in tr]
    s_tr = [slices[i] for i in tr]
    print("when the slice trades, read (tail weight sweep):")
    print(f"  {'tail weight':<11}{'tail auc':>9}{'head auc':>9}{'agg auc':>9}")
    for tail_w in (1.0, 2.0, 3.0, 4.0, 5.0):
        w = fit_weighted(x_tr, c_tr, s_tr, tail_w)
        ps = [sigmoid(sum(w[i] * xs[j][i] for i in range(8)) + w[8]) for j in te]
        tail_auc = auc([p for p, j in zip(ps, te) if slices[j] == "tail"],
                       [y_click[j] for p, j in zip(ps, te) if slices[j] == "tail"])
        head_auc = auc([p for p, j in zip(ps, te) if slices[j] == "head"],
                       [y_click[j] for p, j in zip(ps, te) if slices[j] == "head"])
        agg = auc(ps, [y_click[j] for j in te])
        print(f"  {tail_w:<11.1f}{tail_auc:>9.3f}{head_auc:>9.3f}{agg:>9.3f}")
    print()
    print("reading: the first weight steps buy the tail cheaply and the")
    print("aggregate AUC does not move, so a model owner watching only the")
    print("aggregate cannot tell whether the tail is being bought or sold.")
    print("the frontier saturates as the tail weight keeps rising, and where")
    print("to sit is a product trade -- the tail slice's experience against")
    print("the head slice's -- that no single model metric decides.")


if __name__ == "__main__":
    main()
