"""Holds the model fixed and swaps the representation, on all three endpoints.

Stages 01, 03, and 04 compared (ten descriptors + logistic regression)
against (SMILES characters + a small trained model). Two things differ
between those arms at once -- what the molecule is turned into, and what
learns from it -- so a win belongs to the pair, not to either half. Stage 05
closed the scarcity question and said the next stage would need a different
candidate explanatory variable. This is that variable: the representation.

The design holds the learner constant. Stage 01's own
`fit_logistic_regression` is imported and run unmodified over two different
feature matrices for the same molecules, the same scaffold split, and the
same three seeds:

    descriptors  -> 10 physicochemical floats  -> logistic regression
    fingerprint  -> 2048 substructure bits     -> logistic regression

The difference between those two is attributable to the representation
alone. Set beside the already-measured trained-model arm, it says whether
the descriptor baseline was winning because ten numbers are the right
description of a molecule, or because logistic regression on any fixed
representation was beating this particular small learned model.

Splits are not rebuilt. Each endpoint's train/test CSVs were written by the
stage that introduced it -- rebuilding them here would re-run a scaffold
split whose seed and fraction are already recorded, and any drift in that
would land inside a difference meant to isolate one variable.

Usage:
    uv run --group chem python run_representation_grid.py
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

import numpy as np

MISSION = Path(__file__).resolve().parents[2]
STAGE01_CORE = MISSION / "01-descriptor-baseline-and-model" / "core"
sys.path.insert(0, str(STAGE01_CORE))

from circular_fingerprint import N_BITS, RADIUS, density_report, load_fingerprint_matrix
from descriptor_baseline import fit_logistic_regression, sigmoid, standardize
from descriptors import load_descriptor_matrix
from metrics import roc_auc

SEEDS = [0, 1, 2]

# The width sweep exists because the first run of this stage produced a
# fingerprint train AUC of 0.9995 against a test AUC of 0.6534 -- the model
# had memorized the training set, so "the representation is worse" and "2048
# unregularized features overfit 4,600 molecules" both predicted exactly the
# observed number. Narrowing the fold reduces capacity without changing the
# algorithm, which separates them.
BIT_WIDTHS = [64, 256, 1024, 2048]

# Each endpoint's split lives with the stage that introduced it, and each of
# those stages recorded its own scaffold-split seed and fraction.
ENDPOINTS = [
    ("SR-MMP", MISSION / "00-dataset-and-property" / "data"),
    ("NR-PPAR-gamma", MISSION / "03-second-endpoint" / "data"),
    ("NR-ER", MISSION / "04-third-endpoint" / "data"),
]


def evaluate(train_x, train_y, test_x, test_y, seed: int) -> tuple[float, float]:
    """Stage 01's own standardization, optimizer, and metric, returning train
    AUC beside test AUC.

    Standardizing a 0/1 bit matrix is not a no-op -- it centres each column on
    its corpus frequency, which is what keeps a rare substructure from being
    drowned by a common one under a single global learning rate.

    Train AUC is reported because the two representations differ by more than
    two orders of magnitude in width (10 versus 2048 features against roughly
    5,000 training molecules), and unregularized logistic regression at that
    width can fit the training set far better while generalizing worse. Without
    the train number, a low fingerprint test AUC cannot be told apart from
    overfitting, and this stage would be attributing to the representation
    something the capacity did."""
    train_s, test_s = standardize(train_x, test_x)
    w, b = fit_logistic_regression(train_s, train_y, seed)
    return (
        roc_auc(train_y, sigmoid(train_s @ w + b)),
        roc_auc(test_y, sigmoid(test_s @ w + b)),
    )


def run_endpoint(name: str, data_dir: Path) -> dict:
    train_csv, test_csv = data_dir / "train.csv", data_dir / "test.csv"

    t0 = time.perf_counter()
    d_train_x, d_train_y, d_dropped_train = load_descriptor_matrix(train_csv)
    d_test_x, d_test_y, d_dropped_test = load_descriptor_matrix(test_csv)
    descriptor_featurize_s = time.perf_counter() - t0

    t1 = time.perf_counter()
    f_train_x, f_train_y, f_dropped_train = load_fingerprint_matrix(train_csv)
    f_test_x, f_test_y, f_dropped_test = load_fingerprint_matrix(test_csv)
    fingerprint_featurize_s = time.perf_counter() - t1

    # Both representations must be describing the same molecules, or the two
    # AUCs are computed over different test sets and the difference between
    # them means nothing.
    assert np.array_equal(d_train_y, f_train_y), f"{name}: train labels differ between representations"
    assert np.array_equal(d_test_y, f_test_y), f"{name}: test labels differ between representations"
    assert d_dropped_train == f_dropped_train and d_dropped_test == f_dropped_test, (
        f"{name}: the two featurizers dropped different molecules"
    )

    descriptor_pairs = [evaluate(d_train_x, d_train_y, d_test_x, d_test_y, s) for s in SEEDS]
    fingerprint_pairs = [evaluate(f_train_x, f_train_y, f_test_x, f_test_y, s) for s in SEEDS]
    descriptor_train_aucs = [p[0] for p in descriptor_pairs]
    fingerprint_train_aucs = [p[0] for p in fingerprint_pairs]
    descriptor_aucs = [p[1] for p in descriptor_pairs]
    fingerprint_aucs = [p[1] for p in fingerprint_pairs]

    d_mean, f_mean = statistics.mean(descriptor_aucs), statistics.mean(fingerprint_aucs)
    d_spread = max(descriptor_aucs) - min(descriptor_aucs)
    f_spread = max(fingerprint_aucs) - min(fingerprint_aucs)
    gap = f_mean - d_mean
    larger_spread = max(d_spread, f_spread)

    return {
        "endpoint": name,
        "split_dir": str(data_dir.relative_to(MISSION.parent.parent)),
        "n_train": len(d_train_y),
        "n_test": len(d_test_y),
        "train_positive_rate": float(d_train_y.mean()),
        "n_features": {"descriptors": int(d_train_x.shape[1]), "fingerprint": int(f_train_x.shape[1])},
        "featurize_wall_clock_s": {
            "descriptors": descriptor_featurize_s,
            "fingerprint": fingerprint_featurize_s,
        },
        "fingerprint_density_train": density_report(f_train_x),
        "descriptor_train_auc_per_seed": descriptor_train_aucs,
        "fingerprint_train_auc_per_seed": fingerprint_train_aucs,
        "descriptor_train_minus_test_auc": statistics.mean(descriptor_train_aucs)
        - statistics.mean(descriptor_aucs),
        "fingerprint_train_minus_test_auc": statistics.mean(fingerprint_train_aucs)
        - statistics.mean(fingerprint_aucs),
        "descriptor_auc_per_seed": descriptor_aucs,
        "fingerprint_auc_per_seed": fingerprint_aucs,
        "descriptor_auc_mean": d_mean,
        "fingerprint_auc_mean": f_mean,
        "descriptor_auc_spread": d_spread,
        "fingerprint_auc_spread": f_spread,
        "gap_fingerprint_minus_descriptor": gap,
        # The same decision rule stage 05 used: a gap smaller than the larger
        # of the two seed spreads is not a result.
        "verdict": (
            "fingerprint wins beyond spread"
            if gap > larger_spread
            else "descriptor wins beyond spread"
            if -gap > larger_spread
            else "inconclusive (gap inside spread)"
        ),
    }


def bit_width_sweep(name: str, data_dir: Path) -> list[dict]:
    """Same molecules, same learner, same seeds -- only the fold width moves.

    If the fingerprint arm's test AUC climbs as the width falls, capacity was
    the binding problem and the wide result says nothing about the
    representation. If it stays flat or falls, the representation really is
    carrying less signal than ten descriptors on this endpoint.
    """
    train_csv, test_csv = data_dir / "train.csv", data_dir / "test.csv"
    out = []
    for width in BIT_WIDTHS:
        train_x, train_y, _ = load_fingerprint_matrix(train_csv, n_bits=width)
        test_x, test_y, _ = load_fingerprint_matrix(test_csv, n_bits=width)
        pairs = [evaluate(train_x, train_y, test_x, test_y, s) for s in SEEDS]
        train_aucs = [p[0] for p in pairs]
        test_aucs = [p[1] for p in pairs]
        out.append({
            "n_bits": width,
            "columns_ever_set": density_report(train_x)["columns_ever_set"],
            "train_auc_mean": statistics.mean(train_aucs),
            "test_auc_mean": statistics.mean(test_aucs),
            "test_auc_spread": max(test_aucs) - min(test_aucs),
            "train_minus_test": statistics.mean(train_aucs) - statistics.mean(test_aucs),
        })
        print(
            f"  {width:>5} bits: train {out[-1]['train_auc_mean']:.4f} "
            f"test {out[-1]['test_auc_mean']:.4f} "
            f"gap {out[-1]['train_minus_test']:.4f}",
            flush=True,
        )
    return out


def main() -> None:
    runs_dir = Path(__file__).resolve().parents[1] / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    results = []
    for name, data_dir in ENDPOINTS:
        print(f"=== {name}", flush=True)
        result = run_endpoint(name, data_dir)
        results.append(result)
        print(
            f"  descriptors {result['descriptor_auc_mean']:.4f} "
            f"(spread {result['descriptor_auc_spread']:.4f})  "
            f"fingerprint {result['fingerprint_auc_mean']:.4f} "
            f"(spread {result['fingerprint_auc_spread']:.4f})  "
            f"-> {result['verdict']}",
            flush=True,
        )

    sweep_endpoint, sweep_dir = ENDPOINTS[0]
    print(f"\n=== bit-width sweep on {sweep_endpoint}", flush=True)
    sweep = bit_width_sweep(sweep_endpoint, sweep_dir)

    verdicts = {r["endpoint"]: r["verdict"] for r in results}
    payload = {
        "stage": "06-model-or-representation",
        "question": "does the representation, holding the learner fixed, change which arm wins",
        "learner": "stage 01's fit_logistic_regression, unmodified",
        "fingerprint": {"radius": RADIUS, "n_bits": N_BITS, "implementation": "core/circular_fingerprint.py"},
        "seeds": SEEDS,
        "endpoints": results,
        "bit_width_sweep": {"endpoint": sweep_endpoint, "widths": sweep},
        "verdicts": verdicts,
        "fingerprint_wins_on": [k for k, v in verdicts.items() if v.startswith("fingerprint")],
        "wall_clock_s": time.perf_counter() - t0,
        "compute_lane": "local CPU",
        "dollar_cost": 0.0,
        "note": "n=3 endpoints and n=3 seeds; per-endpoint verdicts only, no claim across endpoints.",
    }
    out = runs_dir / "representation-grid.json"
    out.write_text(json.dumps(payload, indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
