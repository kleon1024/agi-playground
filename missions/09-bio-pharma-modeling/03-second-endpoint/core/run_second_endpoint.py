"""Does the SR-MMP finding (descriptor baseline beats the trained model)
generalize to a different Tox21 endpoint?

This stage does not reimplement anything: it imports stage 00's split
functions and stage 01's baseline/model training functions directly, and
runs them against NR-PPAR-gamma instead of SR-MMP. NR-PPAR-gamma is picked
because stage 00's own per-endpoint balance table (in
../../00-dataset-and-property/runs/2026-08-01-dataset-and-split.md) makes it
the most different pick available: 2.9% positive over 6,450 labeled
compounds, versus SR-MMP's 15.8% over 5,810 -- roughly 5x more imbalanced and
a materially different labeled count, so a repeat here is a genuine test of
generality rather than a near-duplicate of stage 01's own split.

Same protocol throughout: scaffold split (train-frac 0.8, split-seed 0),
3 training seeds each for the descriptor baseline and the trained model.

Usage:
    uv run --group torch --group chem python run_second_endpoint.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

STAGE00_CORE = Path(__file__).resolve().parents[2] / "00-dataset-and-property" / "core"
STAGE01_CORE = Path(__file__).resolve().parents[2] / "01-descriptor-baseline-and-model" / "core"
sys.path.insert(0, str(STAGE00_CORE))
sys.path.insert(0, str(STAGE01_CORE))

from descriptor_baseline import run as run_descriptor_baseline
from prepare_dataset import (
    download,
    label_stats,
    load_endpoint,
    murcko_scaffolds,
    scaffold_split,
    sha256_of,
    write_split,
)
from smiles_model import train_and_eval

ENDPOINT = "NR-PPAR-gamma"
URL = "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/tox21.csv.gz"
TRAIN_FRAC = 0.8
SPLIT_SEED = 0
SEEDS = [0, 1, 2]


def build_split(out_dir: Path) -> dict:
    t0 = time.time()
    csv_path = download(URL, out_dir / "raw")
    dataset_hash = sha256_of(csv_path)

    all_stats = label_stats(csv_path)
    compounds = load_endpoint(csv_path, ENDPOINT)
    scaffolds, dropped = murcko_scaffolds(compounds)
    kept = [c for c in compounds if c.mol_id in scaffolds]

    train, test, split_stats = scaffold_split(kept, scaffolds, TRAIN_FRAC, SPLIT_SEED)
    write_split(out_dir / "train.csv", train, scaffolds)
    write_split(out_dir / "test.csv", test, scaffolds)

    def positive_rate(rows) -> float:
        return sum(c.label for c in rows) / len(rows) if rows else 0.0

    summary = {
        "endpoint": ENDPOINT,
        "url": URL,
        "dataset_sha256": dataset_hash,
        "n_labeled_for_endpoint": len(compounds),
        "n_dropped_unparseable_smiles": len(dropped),
        "dropped_mol_ids": dropped,
        "endpoint_label_stats": all_stats[ENDPOINT],
        "train_frac_target": TRAIN_FRAC,
        "split_seed": SPLIT_SEED,
        "n_train": len(train),
        "n_test": len(test),
        "train_positive_rate": positive_rate(train),
        "test_positive_rate": positive_rate(test),
        "scaffold_split_stats": split_stats,
        "wall_clock_seconds": time.time() - t0,
    }
    (out_dir / "split_summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def main() -> None:
    data_dir = Path(__file__).resolve().parents[1] / "data"
    runs_dir = Path(__file__).resolve().parents[1] / "runs"
    data_dir.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)

    split_summary = build_split(data_dir)
    print(json.dumps(split_summary, indent=2))

    train_csv, test_csv = data_dir / "train.csv", data_dir / "test.csv"

    descriptor_results = []
    for seed in SEEDS:
        result = run_descriptor_baseline(train_csv, test_csv, seed)
        (runs_dir / f"descriptor-seed{seed}.json").write_text(json.dumps(result, indent=2))
        descriptor_results.append(result)
        print(f"descriptor seed {seed}: test_roc_auc={result['test_roc_auc']:.4f}")

    model_results = []
    for seed in SEEDS:
        result = train_and_eval(train_csv, test_csv, seed, steps=600)
        (runs_dir / f"model-seed{seed}.json").write_text(json.dumps(result, indent=2))
        model_results.append(result)
        print(f"model seed {seed}: test_roc_auc={result['test_roc_auc']:.4f}")

    desc_aucs = [r["test_roc_auc"] for r in descriptor_results]
    model_aucs = [r["test_roc_auc"] for r in model_results]
    print(json.dumps({
        "endpoint": ENDPOINT,
        "descriptor_mean": sum(desc_aucs) / len(desc_aucs),
        "descriptor_spread": max(desc_aucs) - min(desc_aucs),
        "model_mean": sum(model_aucs) / len(model_aucs),
        "model_spread": max(model_aucs) - min(model_aucs),
    }, indent=2))


if __name__ == "__main__":
    main()
