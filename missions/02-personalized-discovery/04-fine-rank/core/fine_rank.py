"""Fine-rank: one shared model, several predicted objectives — click,
completion, satisfaction, dwell — because no single one of them is what you
actually want to optimize, and stage 05 needs all of them to make that
optimization explicit rather than accidental.

Two mechanisms carry this file, and each has a failure mode worth causing on
purpose before trusting the fix:

**Multi-task interference.** A shared trunk feeding several task-specific
heads is attractive because features useful for "will they click" are mostly
also useful for "will they stay" — reuse is free accuracy. It is not free by
default: tasks disagree on how much of the training signal they get
(`click` is observed on every impression, a satisfaction label might come
from a rare post-session survey) and on what scale their loss lives on (a
bounded probability versus dwell time in raw seconds). A shared trunk trained
by naive summed loss lets whichever task has the largest gradient magnitude
dominate the representation, starving the others — a failure usually called
negative transfer, and it is reproduced below, not just described.

**Calibration.** A ranking-only model can get every pairwise order right while
its output numbers mean nothing — a predicted "0.9" and a predicted "0.3" can
both be systematically off by the same miscalibration and the ranking survives
untouched, because a monotonic transform preserves order within one task. It
stops being harmless the moment stage 05 combines *different* tasks' numbers
arithmetically: `0.5*p_click + 0.5*p_satisfy` is only a meaningful blend if
both numbers are on the same true-probability scale. This file measures that
gap directly with expected calibration error (ECE), before and after a
Platt-scaling fix.

Everything here is pure Python — no numpy, no autodiff — because a hand-rolled
forward/backward pass over a two-layer network is small enough to read in
full, and reading it in full is the point of `core/`.

Run:  python fine_rank.py
      python fine_rank.py --epochs 40 --hidden 12
"""

from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass

Vector = list[float]
Matrix = list[list[float]]

TASKS = ("click", "completion", "satisfaction", "dwell")
BINARY_TASKS = ("click", "completion", "satisfaction")
# How often each label is actually observed, in this order: click is logged on
# every impression; completion needs a click first and is itself often
# missing; satisfaction is a rare post-session survey. This is the sparsity
# gradient that makes naive equal-weighting dangerous.
OBSERVE_RATE = {"click": 1.0, "completion": 0.45, "satisfaction": 0.10, "dwell": 0.55}
DWELL_SCALE = 300.0  # seconds; used only to normalize the "balanced" run


# ---------------------------------------------------------------------------
# Synthetic data: one shared latent "fit" per impression drives all four
# labels, each through a different, noisy, partially-observed lens — the
# reason no single label is "the" objective is that each is a lossy view of
# the same underlying thing you actually care about.
# ---------------------------------------------------------------------------


@dataclass
class Example:
    features: Vector
    labels: dict[str, float]  # only keys with an observed label are present


def make_dataset(n: int, seed: int) -> list[Example]:
    rng = random.Random(seed)
    examples = []
    for _ in range(n):
        features = [rng.uniform(-1, 1) for _ in range(5)]
        fit = math.tanh(0.9 * features[0] + 0.6 * features[1] - 0.4 * features[2])
        p_click = sigmoid(3.0 * fit + rng.gauss(0, 0.3))
        p_completion = sigmoid(2.5 * fit + 0.5 * features[3] + rng.gauss(0, 0.4))
        p_satisfaction = sigmoid(2.0 * fit + 0.8 * features[4] + rng.gauss(0, 0.5))
        dwell_seconds = max(0.0, 120 * (0.5 * fit + 0.5) + rng.gauss(0, 25))

        labels: dict[str, float] = {}
        if rng.random() < OBSERVE_RATE["click"]:
            labels["click"] = 1.0 if rng.random() < p_click else 0.0
        if rng.random() < OBSERVE_RATE["completion"]:
            labels["completion"] = 1.0 if rng.random() < p_completion else 0.0
        if rng.random() < OBSERVE_RATE["satisfaction"]:
            labels["satisfaction"] = 1.0 if rng.random() < p_satisfaction else 0.0
        if rng.random() < OBSERVE_RATE["dwell"]:
            labels["dwell"] = dwell_seconds

        examples.append(Example(features=features, labels=labels))
    return examples


# ---------------------------------------------------------------------------
# A tiny shared trunk + per-task linear heads, trained by hand.
# ---------------------------------------------------------------------------


def sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


@dataclass
class Model:
    w1: Matrix  # hidden x input
    b1: Vector  # hidden
    heads: dict[str, tuple[Vector, float]]  # task -> (weights over hidden, bias)


def init_model(input_dim: int, hidden_dim: int, seed: int) -> Model:
    rng = random.Random(seed)
    scale = (1.0 / input_dim) ** 0.5
    w1 = [[rng.uniform(-scale, scale) for _ in range(input_dim)] for _ in range(hidden_dim)]
    b1 = [0.0] * hidden_dim
    heads = {t: ([rng.uniform(-0.1, 0.1) for _ in range(hidden_dim)], 0.0) for t in TASKS}
    return Model(w1=w1, b1=b1, heads=heads)


def forward_trunk(model: Model, x: Vector) -> Vector:
    return [math.tanh(sum(w * xi for w, xi in zip(row, x)) + b) for row, b in zip(model.w1, model.b1)]


def train_step(
    model: Model, example: Example, lr: float, balanced: bool
) -> None:
    h = forward_trunk(model, example.features)
    grad_h = [0.0] * len(h)

    for task in TASKS:
        if task not in example.labels:
            continue
        w, b = model.heads[task]
        z = sum(wi * hi for wi, hi in zip(w, h)) + b
        target = example.labels[task]

        if task in BINARY_TASKS:
            pred = sigmoid(z)
            # d(BCE)/dz = pred - target, the standard sigmoid+BCE gradient.
            dz = pred - target
            task_weight = 1.0  # binary losses already share a comparable scale
        else:
            # dwell: identity output, squared error. In "naive" mode the target
            # stays in raw seconds, so a single example's gradient can be two
            # orders of magnitude larger than a binary task's — that gap is
            # the entire point of the naive/balanced comparison.
            scaled_target = target / DWELL_SCALE if balanced else target
            pred = z
            dz = 2.0 * (pred - scaled_target)
            task_weight = 0.3 if balanced else 1.0

        dz *= task_weight
        new_w = [wi - lr * dz * hi for wi, hi in zip(w, h)]
        new_b = b - lr * dz
        model.heads[task] = (new_w, new_b)
        for j in range(len(h)):
            grad_h[j] += dz * w[j]  # use the pre-update head weights

    for j in range(len(h)):
        dtanh = 1 - h[j] ** 2
        delta = grad_h[j] * dtanh
        for i in range(len(example.features)):
            model.w1[j][i] -= lr * delta * example.features[i]
        model.b1[j] -= lr * delta


def train(examples: list[Example], hidden: int, epochs: int, lr: float, balanced: bool, seed: int) -> Model:
    model = init_model(input_dim=5, hidden_dim=hidden, seed=seed)
    rng = random.Random(seed + 1)
    for _ in range(epochs):
        order = list(range(len(examples)))
        rng.shuffle(order)
        for i in order:
            train_step(model, examples[i], lr, balanced)
    return model


def predict(model: Model, features: Vector) -> dict[str, float]:
    h = forward_trunk(model, features)
    out = {}
    for task in TASKS:
        w, b = model.heads[task]
        z = sum(wi * hi for wi, hi in zip(w, h)) + b
        out[task] = sigmoid(z) if task in BINARY_TASKS else z
    return out


# ---------------------------------------------------------------------------
# Evaluation: a pairwise ranking accuracy for binary tasks (a manual AUC), a
# Pearson correlation for dwell, and calibration error for click.
# ---------------------------------------------------------------------------


def pairwise_accuracy(scores: Vector, labels: Vector) -> float | None:
    pos = [s for s, y in zip(scores, labels) if y == 1.0]
    neg = [s for s, y in zip(scores, labels) if y == 0.0]
    if not pos or not neg:
        return None
    wins = sum(1 for p in pos for n in neg if p > n)
    ties = sum(1 for p in pos for n in neg if p == n)
    total = len(pos) * len(neg)
    return (wins + 0.5 * ties) / total


def pearson(a: Vector, b: Vector) -> float | None:
    n = len(a)
    if n < 2:
        return None
    mean_a, mean_b = sum(a) / n, sum(b) / n
    cov = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    var_a = sum((x - mean_a) ** 2 for x in a)
    var_b = sum((y - mean_b) ** 2 for y in b)
    if var_a == 0 or var_b == 0:
        return None
    return cov / math.sqrt(var_a * var_b)


def expected_calibration_error(probs: Vector, labels: Vector, bins: int = 10) -> float:
    buckets: list[list[tuple[float, float]]] = [[] for _ in range(bins)]
    for p, y in zip(probs, labels):
        idx = min(bins - 1, int(p * bins))
        buckets[idx].append((p, y))
    n = len(probs)
    ece = 0.0
    for bucket in buckets:
        if not bucket:
            continue
        avg_pred = sum(p for p, _ in bucket) / len(bucket)
        avg_true = sum(y for _, y in bucket) / len(bucket)
        ece += (len(bucket) / n) * abs(avg_pred - avg_true)
    return ece


def fit_platt_scaling(logits: Vector, labels: Vector, lr: float = 0.05, steps: int = 500) -> tuple[float, float]:
    """1-D logistic regression on the raw logit: p = sigmoid(a*z + b). This is
    the classic Platt-scaling fix — cheap, and sufficient when miscalibration
    is roughly a scale-and-shift of the logit, which is the common case for a
    model trained with the right loss but the wrong effective sample weight.
    """
    a, b = 1.0, 0.0
    n = len(logits)
    for _ in range(steps):
        grad_a = grad_b = 0.0
        for z, y in zip(logits, labels):
            pred = sigmoid(a * z + b)
            err = pred - y
            grad_a += err * z
            grad_b += err
        a -= lr * grad_a / n
        b -= lr * grad_b / n
    return a, b


def logit(p: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def run_demo(hidden: int, epochs: int, lr: float, seed: int) -> None:
    train_examples = make_dataset(1500, seed)
    val_examples = make_dataset(400, seed + 999)
    calib_examples = make_dataset(400, seed + 1999)  # held out separately from validation

    print(f"trunk hidden={hidden}, epochs={epochs}, lr={lr}\n")
    print("negative transfer: naive equal weighting vs. scale-normalized weighting")
    print(f"{'task':<14}{'naive':>10}{'balanced':>12}")

    naive_model = train(train_examples, hidden, epochs, lr, balanced=False, seed=seed)
    balanced_model = train(train_examples, hidden, epochs, lr, balanced=True, seed=seed)

    for task in TASKS:
        row = [task]
        for model in (naive_model, balanced_model):
            preds = [predict(model, ex.features)[task] for ex in val_examples if task in ex.labels]
            labels = [ex.labels[task] for ex in val_examples if task in ex.labels]
            if task in BINARY_TASKS:
                metric = pairwise_accuracy(preds, labels)
                row.append("n/a" if metric is None else f"{metric:.3f}")
            else:
                metric = pearson(preds, labels)
                row.append("n/a" if metric is None else f"{metric:.3f}")
        print(f"{row[0]:<14}{row[1]:>10}{row[2]:>12}")

    print(
        "\n(binary tasks: pairwise ranking accuracy, 0.5 = chance, 1.0 = perfect."
        "\n dwell: Pearson correlation between predicted and true seconds.)"
    )

    # Calibration on the balanced model's click head.
    click_examples = [ex for ex in calib_examples if "click" in ex.labels]
    logits = []
    labels = []
    for ex in click_examples:
        h = forward_trunk(balanced_model, ex.features)
        w, b = balanced_model.heads["click"]
        z = sum(wi * hi for wi, hi in zip(w, h)) + b
        logits.append(z)
        labels.append(ex.labels["click"])

    raw_probs = [sigmoid(z) for z in logits]
    ece_before = expected_calibration_error(raw_probs, labels)

    a, b = fit_platt_scaling(logits, labels)
    calibrated_probs = [sigmoid(a * z + b) for z in logits]
    ece_after = expected_calibration_error(calibrated_probs, labels)

    print(f"\ncalibration (click head, {len(click_examples)} held-out examples):")
    print(f"  ECE before Platt scaling   {ece_before:.4f}")
    print(f"  ECE after  Platt scaling   {ece_after:.4f}  (a={a:.3f}, b={b:.3f})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hidden", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run_demo(args.hidden, args.epochs, args.lr, args.seed)


if __name__ == "__main__":
    main()
