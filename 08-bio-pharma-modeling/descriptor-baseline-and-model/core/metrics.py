"""ROC-AUC from scratch, via the Mann-Whitney U statistic.

No framework beyond `numpy` (already pulled in transitively by RDKit and
torch) computes this: rank every score, sum the ranks of the positive class,
subtract the minimum that sum could be, and divide by the number of
positive/negative pairs -- the number of times a random positive scores above
a random negative, which is exactly what ROC-AUC measures.
"""

from __future__ import annotations

import numpy as np


def roc_auc(y_true: np.ndarray, scores: np.ndarray) -> float:
    y_true = np.asarray(y_true)
    scores = np.asarray(scores)
    n_pos = int(y_true.sum())
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        raise ValueError("roc_auc undefined with only one class present")

    order = np.argsort(scores)
    ranks = np.empty(len(scores))
    ranks[order] = np.arange(1, len(scores) + 1)
    # Average tied ranks so identical scores split the credit, matching the
    # standard rank-sum AUC formula.
    _, inverse, counts = np.unique(scores, return_inverse=True, return_counts=True)
    rank_sums = np.zeros(len(counts))
    np.add.at(rank_sums, inverse, ranks)
    avg_rank_per_score = rank_sums / counts
    ranks = avg_rank_per_score[inverse]

    sum_ranks_pos = ranks[y_true == 1].sum()
    return (sum_ranks_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def seed_spread(values: list[float]) -> dict:
    arr = np.asarray(values)
    return {
        "mean": float(arr.mean()),
        "std": float(arr.std(ddof=0)),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "spread": float(arr.max() - arr.min()),
    }
