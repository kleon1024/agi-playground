"""Negative transfer, measured: shared trunk vs single-task, balanced or not.

Stage 04's multi-objective model has one shared trunk and one head per
task, and its recorded run measured a weighting effect. This script measures
the harder question directly: for each objective, does training the shared
trunk on ALL tasks beat training it on that task ALONE? The difference is
negative (or positive) transfer, per objective. The balanced flag is the
second axis — the recorded run's naive-vs-balanced finding, re-measured on
the transfer grid.

The single-task loop mirrors the core's train_step math for one task only;
everything else is imported.

Run:
    uv run python core/transfer_grid.py
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))

from fine_rank import (
    DWELL_SCALE,
    TASKS,
    forward_trunk,
    init_model,
    make_dataset,
    pairwise_accuracy,
    predict,
    train_step,
)


def train_single(model, examples, task, lr, epochs, seed):
    rng = random.Random(seed + 1)
    for _ in range(epochs):
        order = list(range(len(examples)))
        rng.shuffle(order)
        for i in order:
            ex = examples[i]
            if task not in ex.labels:
                continue
            h = forward_trunk(model, ex.features)
            w, b = model.heads[task]
            z = sum(wi * hi for wi, hi in zip(w, h)) + b
            target = ex.labels[task]
            if task in ("click", "completion", "satisfaction"):
                from math import exp

                pred = 1 / (1 + exp(-z))
                dz = pred - target
            else:
                scaled = target / DWELL_SCALE
                dz = 2.0 * (z - scaled) * 0.3
            new_w = [wi - lr * dz * hi for wi, hi in zip(w, h)]
            model.heads[task] = (new_w, b - lr * dz)
            for j in range(len(h)):
                dtanh = 1 - h[j] ** 2
                delta = dz * w[j] * dtanh
                for k in range(len(ex.features)):
                    model.w1[j][k] -= lr * delta * ex.features[k]
                model.b1[j] -= lr * delta


def evaluate(model, examples) -> dict[str, float]:
    scores = {t: [] for t in TASKS}
    labels = {t: [] for t in TASKS}
    for ex in examples:
        preds = predict(model, ex.features)
        for t in TASKS:
            if t in ex.labels:
                scores[t].append(preds[t])
                labels[t].append(ex.labels[t])
    out = {}
    for t in TASKS:
        acc = pairwise_accuracy(scores[t], labels[t])
        if acc is not None:
            out[t] = acc
    return out


def main() -> None:
    examples = make_dataset(200, seed=42)
    print(f"{'task':<13} {'balanced':>9} {'multi':>7} {'single':>8} {'transfer':>9}")
    for balanced in (False, True):
        for task in TASKS:
            multi = init_model(5, 8, seed=7)
            for _ in range(40):
                order = list(range(len(examples)))
                random.Random(8).shuffle(order)
                for i in order:
                    train_step(multi, examples[i], 0.02, balanced)
            single = init_model(5, 8, seed=7)
            train_single(single, examples, task, 0.02, 40, 8)
            m = evaluate(multi, examples).get(task, 0.0)
            s = evaluate(single, examples).get(task, 0.0)
            transfer = m - s
            print(f"{task:<13} {balanced!s:>9} {m:>7.3f} {s:>8.3f} {transfer:>+9.3f}")


if __name__ == "__main__":
    main()
