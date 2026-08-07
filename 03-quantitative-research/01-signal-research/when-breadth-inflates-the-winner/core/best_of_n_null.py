"""How much does search breadth inflate the best IC you see?

Stage 01's recorded run searched 32 variants and found an in-sample winner of
IC 0.0947; its permutation null said 95 of 300 no-edge searches matched or
beat that. This chapter asks the next question: the null was measured at
*32* candidates. What does the same null look like at 256, 1,024, or 4,096
candidates — the breadth a real search over a library of ideas produces?

The answer is a measured curve, not a formula on a whiteboard. For each grid
size N, this script draws N pure-noise candidate signals (standard-normal
exposures per name, fixed across dates) and scores them against the *same*
within-date permuted forward returns stage 01 used, replicating `--replicates`
times. Each replicate reports the best-of-N IC, so the output is the
distribution of "the winner of a search that tried N noise ideas."

It reuses stage 01's fetch, forward-return construction, and permutation
semantics verbatim; only the candidate generator differs (pure noise instead
of momentum/volatility/value families). The N=32 point is a calibration
check: the recorded null's best-of-32 mean was 0.0818, and the synthetic
number here will not equal it exactly — the real grid's candidates are
correlated with each other, the synthetic ones are i.i.d. — and the chapter
reads that gap rather than hiding it.

Run:
    uv run python core/best_of_n_null.py --replicates 200
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))

from signal_search import (
    MIN_NAMES_PER_DATE,
    UNIVERSE,
    build_forward_returns,
    fetch_universe,
    month_end_dates,
    permute_forward_returns,
)


def rankdata_rows(x: np.ndarray) -> np.ndarray:
    """Average ranks along the last axis, mirroring signal_search._rank.

    `x` is (..., N). Returns ranks with ties averaged, same convention as the
    stage's Spearman IC. For the noise candidates ties are impossible (they
    are continuous draws); the returns matrix can contain ties, so averaging
    matters there.
    """
    n = x.shape[-1]
    leading = x.shape[:-1]
    order = np.argsort(x, axis=-1, kind="stable")
    # ranks in sorted order: position k holds the rank of the k-th smallest
    ranks_sorted = np.broadcast_to(np.arange(1, n + 1, dtype=np.float64), x.shape)
    sorted_x = np.take_along_axis(x, order, axis=-1)
    # equal values share a run id; average their ranks per run
    diff = np.concatenate(
        [np.ones(leading + (1,), dtype=bool), sorted_x[..., 1:] != sorted_x[..., :-1]],
        axis=-1,
    )
    run_ids = np.cumsum(diff, axis=-1) - 1
    flat_ids = run_ids.reshape(-1)
    flat_ranks = ranks_sorted.reshape(-1)
    sums = np.zeros(flat_ids.max() + 1, dtype=np.float64)
    np.add.at(sums, flat_ids, flat_ranks)
    counts = np.bincount(flat_ids)
    avg_sorted = (sums / np.maximum(counts, 1))[flat_ids].reshape(x.shape)
    # map back to original positions: inv[order[k]] = k
    inv = np.empty_like(order)
    np.put_along_axis(
        inv, order, np.broadcast_to(np.arange(n), x.shape), axis=-1
    )
    return np.take_along_axis(avg_sorted, inv, axis=-1)


def spearman_rows(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Per-row Spearman correlation of x and y along the last axis."""
    rx = rankdata_rows(x)
    ry = rankdata_rows(y)
    rx = rx - rx.mean(axis=-1, keepdims=True)
    ry = ry - ry.mean(axis=-1, keepdims=True)
    cov = (rx * ry).sum(axis=-1)
    var_x = (rx * rx).sum(axis=-1)
    var_y = (ry * ry).sum(axis=-1)
    denom = np.sqrt(var_x * var_y)
    return np.where(denom > 0, cov / denom, 0.0)


def mean_ic_batch(candidates: np.ndarray, returns: np.ndarray) -> np.ndarray:
    """Mean pooled per-date IC for a batch of candidates.

    `candidates` is (K, D, NAMES) and `returns` is (D, NAMES). Returns (K,)
    mean ICs, averaging per-date Spearman ICs across the dates that clear
    `MIN_NAMES_PER_DATE` — the same equal-weighted-per-date mean the stage's
    `evaluate` computes.
    """
    n = returns.shape[-1]
    usable = n >= MIN_NAMES_PER_DATE
    if not usable:
        return np.full(candidates.shape[0], np.nan)
    ics = spearman_rows(candidates, returns[None, :, :])  # (K, D)
    return np.nanmean(ics, axis=-1)


def run() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--range", default="5y", dest="range_")
    ap.add_argument("--replicates", type=int, default=200)
    ap.add_argument("--seed", type=int, default=20260806)
    ap.add_argument("--threshold", type=float, default=0.0947,
                    help="the recorded winner's in-sample IC to benchmark against")
    args = ap.parse_args()

    grid = [32, 256, 1024, 4096]
    rng = random.Random(args.seed)
    np_rng = np.random.default_rng(args.seed)

    print(f"=== fetching {len(UNIVERSE)}-name universe, range={args.range_} ===")
    panels = fetch_universe(args.range_)
    starts = [p.prices[0][0] for p in panels.values()]
    ends = [p.prices[-1][0] for p in panels.values()]
    rebalance_dates = month_end_dates(max(starts), min(ends))
    forward_returns = build_forward_returns(panels, rebalance_dates)
    returns_rows = [row for row in forward_returns if row]
    dates = len(returns_rows)
    names = sorted(returns_rows[0])
    print(f"cross-sections: {dates} dates x {len(names)} names")

    for n_candidates in grid:
        bests: list[float] = []
        for _ in range(args.replicates):
            permuted = permute_forward_returns(returns_rows, rng)
            perm = np.array([[row[n] for n in names] for row in permuted], dtype=np.float64)
            candidates = np_rng.standard_normal((n_candidates, dates, len(names)))
            ics = mean_ic_batch(candidates, perm)
            bests.append(float(np.nanmax(ics)))
        bests = np.array(bests)
        exceeded = float(np.mean(bests >= args.threshold))
        print(
            f"best-of-{n_candidates:>5}: mean {bests.mean():.4f}  "
            f"median {np.median(bests):.4f}  max {bests.max():.4f}  "
            f"P(>={args.threshold:.4f}) {exceeded:.3f}"
        )


if __name__ == "__main__":
    run()
