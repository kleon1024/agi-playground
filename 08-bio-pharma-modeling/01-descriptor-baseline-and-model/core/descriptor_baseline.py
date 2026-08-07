"""Logistic regression over standard RDKit descriptors -- the descriptor
baseline `mission.yaml` names as the control a trained model must beat.

From scratch: batch gradient descent on the standard logistic loss, no
`sklearn`. The only randomness a convex, deterministically-initialized
problem like this has is which order the data is shuffled into fixed-size
minibatches, so the seed varies that (and the zero weight init stays
deterministic) -- reported spread across seeds tests whether that alone moves
the answer, exactly the same question this repository's other missions ask of
non-convex training.

Usage:
    python descriptor_baseline.py --train ../../00-dataset-and-property/data/train.csv \
        --test ../../00-dataset-and-property/data/test.csv --seed 0
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from descriptors import DESCRIPTOR_NAMES, load_descriptor_matrix
from metrics import roc_auc


def standardize(train_x: np.ndarray, test_x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = train_x.mean(axis=0)
    std = train_x.std(axis=0)
    std[std == 0] = 1.0
    return (train_x - mean) / std, (test_x - mean) / std


def sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def fit_logistic_regression(
    X: np.ndarray, y: np.ndarray, seed: int, epochs: int = 300, lr: float = 0.1, batch_size: int = 256
) -> tuple[np.ndarray, float]:
    rng = np.random.default_rng(seed)
    n, d = X.shape
    w = np.zeros(d)
    b = 0.0
    for _epoch in range(epochs):
        order = rng.permutation(n)
        for start in range(0, n, batch_size):
            idx = order[start : start + batch_size]
            xb, yb = X[idx], y[idx]
            p = sigmoid(xb @ w + b)
            grad_w = xb.T @ (p - yb) / len(idx)
            grad_b = float((p - yb).mean())
            w -= lr * grad_w
            b -= lr * grad_b
    return w, b


def run(train_csv: Path, test_csv: Path, seed: int) -> dict:
    t0 = time.time()
    train_x, train_y, train_dropped = load_descriptor_matrix(train_csv)
    test_x, test_y, test_dropped = load_descriptor_matrix(test_csv)
    train_x_std, test_x_std = standardize(train_x, test_x)

    w, b = fit_logistic_regression(train_x_std, train_y.astype(np.float64), seed)
    test_scores = sigmoid(test_x_std @ w + b)
    auc = roc_auc(test_y, test_scores)
    return {
        "seed": seed,
        "n_train": len(train_y),
        "n_test": len(test_y),
        "n_train_dropped": len(train_dropped),
        "n_test_dropped": len(test_dropped),
        "descriptor_names": DESCRIPTOR_NAMES,
        "test_roc_auc": auc,
        "wall_clock_seconds": time.time() - t0,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default="../../00-dataset-and-property/data/train.csv")
    ap.add_argument("--test", default="../../00-dataset-and-property/data/test.csv")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="../runs")
    args = ap.parse_args()

    result = run(Path(args.train), Path(args.test), args.seed)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"descriptor-seed{args.seed}.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
