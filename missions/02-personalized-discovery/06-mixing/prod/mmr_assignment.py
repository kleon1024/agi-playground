"""The production lane for stage 06: the same slate-assembly job, split into
two well-studied problems solved by named algorithms instead of one joint
search over the whole space.

`core/slate_mixing.py` folds "which items" and "what order" into a single
beam search and approximates it. That is not the only decomposition. A
common production shape splits the job in two: first select a diverse
subset of size k with Maximal Marginal Relevance (MMR) -- a classic,
inexpensive re-ranking rule that at each step picks whichever remaining
candidate maximizes relevance minus its similarity to what has already been
chosen -- then, given that fixed set, solve for the position order that
maximizes total position-weighted value, which is exactly a linear
assignment problem: k items to k position weights, one item per slot, one
slot per item. `scipy.optimize.linear_sum_assignment` (the Hungarian
algorithm) solves that exactly, in polynomial time, with no beam width and
no approximation -- because once the subset is fixed, arranging it into
slots by weight is a rearrangement problem with a known optimal answer
(highest value to highest weight), which the solver confirms rather than
searches for. What no algorithm here relieves you of: choosing MMR's
relevance/diversity trade-off, which remains a judgment call, same as
core's diversity decay and category cap.

Requires numpy and scipy, not part of this repository's base dependency
group.

Run:  python mmr_assignment.py
"""

from __future__ import annotations

import argparse

import numpy as np
from scipy.optimize import linear_sum_assignment


def make_catalogue(n: int, seed: int) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """n items, each with a scalar value and a small embedding standing in
    for whatever content or behavioral representation a real system would
    carry. One tight cluster of near-duplicate, high-value embeddings is
    placed on purpose, mirroring core's hand-picked near-identical sports
    items, so MMR has something to actually discipline.
    """
    rng = np.random.default_rng(seed)
    dim = 4
    n_dupes = min(3, n)
    duplicate_cluster = rng.normal(loc=1.0, scale=0.05, size=(n_dupes, dim))
    rest = rng.normal(loc=-1.0, scale=0.4, size=(n - n_dupes, dim))
    embeddings = np.vstack([duplicate_cluster, rest]) if n - n_dupes > 0 else duplicate_cluster
    dupe_values = rng.uniform(0.80, 0.90, size=n_dupes)
    rest_values = rng.uniform(0.30, 0.85, size=max(n - n_dupes, 0))
    values = np.concatenate([dupe_values, rest_values])
    ids = [f"item_{i}" for i in range(n)]
    return embeddings, values, ids


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denom) if denom > 0 else 0.0


def mmr_select(embeddings: np.ndarray, values: np.ndarray, k: int, lam: float) -> list[int]:
    """Maximal Marginal Relevance: at each step, pick the remaining
    candidate maximizing `lam * value - (1 - lam) * max_similarity`, where
    `max_similarity` is against whatever has already been selected.
    `lam=1.0` ignores diversity entirely and degenerates to core's greedy
    top-k; `lam=0.0` ignores value and greedily maximizes spread instead.
    Production systems tune `lam` by search, same as core's diversity decay
    -- no formula picks it for you.
    """
    selected: list[int] = []
    remaining = list(range(len(values)))
    while remaining and len(selected) < k:
        best_idx, best_score = -1, float("-inf")
        for i in remaining:
            max_sim = max((cosine_similarity(embeddings[i], embeddings[j]) for j in selected), default=0.0)
            score = lam * float(values[i]) - (1 - lam) * max_sim
            if score > best_score:
                best_idx, best_score = i, score
        selected.append(best_idx)
        remaining.remove(best_idx)
    return selected


def position_weight(position: int) -> float:
    # The identical curve to core/slate_mixing.py's, restated here so this
    # file runs standalone without importing across the core/prod boundary.
    return 1.0 / float(np.log2(position + 2))


def assign_positions(values: np.ndarray, k: int) -> tuple[list[int], float]:
    """Given k already-selected items' values, find the position order that
    maximizes total position-weighted value as an exact linear assignment
    problem. `cost[i, j] = -(value_i * weight_j)`; minimizing that cost over
    all one-to-one assignments is equivalent to maximizing the weighted
    total, and `linear_sum_assignment` finds the global optimum for it, not
    an approximation.
    """
    weights = np.array([position_weight(p) for p in range(k)])
    cost = -np.outer(values, weights)
    row_ind, col_ind = linear_sum_assignment(cost)
    # row_ind is already [0, 1, ..., k-1] for a square cost matrix; col_ind[i]
    # is the position slot assigned to subset item i. Invert it to read off
    # which subset item occupies each position, in position order.
    item_at_position = sorted(range(k), key=lambda i: col_ind[i])
    total_value = float(-cost[row_ind, col_ind].sum())
    return item_at_position, total_value


def run(n: int, k: int, lam: float, seed: int) -> None:
    embeddings, values, ids = make_catalogue(n, seed)
    print(f"catalogue: {n} items, embedding dim {embeddings.shape[1]}")

    print(f"\nMMR selection, lambda={lam} (1.0 = ignore diversity, 0.0 = ignore value):")
    selected = mmr_select(embeddings, values, k, lam)
    picked_values = [round(float(values[i]), 3) for i in selected]
    print(f"  selected: {[ids[i] for i in selected]}  values={picked_values}")

    print("\nposition assignment via scipy.optimize.linear_sum_assignment (Hungarian algorithm):")
    item_at_position, total_value = assign_positions(values[selected], k)
    ordered_ids = [ids[selected[i]] for i in item_at_position]
    print(f"  slot order: {ordered_ids}")
    print(f"  total position-weighted value: {total_value:.4f} (exact optimum for this fixed subset)")

    print("\ncompare lambda values on the same catalogue:")
    for probe_lam in (1.0, 0.7, 0.4, 0.0):
        probe_selected = mmr_select(embeddings, values, k, probe_lam)
        print(f"  lambda={probe_lam:.1f}: {[ids[i] for i in probe_selected]}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=9)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--lam", type=float, default=0.6)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run(args.n, args.k, args.lam, args.seed)


if __name__ == "__main__":
    main()
