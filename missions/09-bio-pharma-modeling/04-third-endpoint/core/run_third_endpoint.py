"""Does the class-scarcity-drives-variance hypothesis from stage 03 hold at
a third Tox21 endpoint?

Stage 03 found that NR-PPAR-gamma (2.9% positive, 148 positive compounds in
its own training split) produced a trained-model seed-to-seed spread roughly
4x larger than SR-MMP's (15.8% positive, 764 positive compounds in its own
training split), while the convex descriptor baseline's spread barely moved
between the two -- and floated a hypothesis: trained-model variance scales
with positive-class scarcity in a way a convex descriptor fit does not.

This stage does not reimplement anything: same imports from stage 00 and
stage 01 that stage 03 itself used, same protocol (scaffold split,
train-frac 0.8, split-seed 0, 3 training seeds), a third endpoint.

Endpoint choice, and why it does not sit outside the already-tested range:
stage 00's own 12-endpoint balance table (see
../../00-dataset-and-property/runs/2026-08-01-dataset-and-split.md) shows
NR-PPAR-gamma (2.9%) is already the single most imbalanced endpoint in the
whole panel, and SR-MMP (15.8%) is tied for the most balanced with SR-ARE
(16.2%, already rejected by stage 03 as a near-duplicate of SR-MMP). No
endpoint exists that is more extreme in either direction than what stage 03
already tested. The genuinely new information available is therefore
whether the relationship holds *in between* the two already-tested points,
not further outside them. NR-ER is picked: 12.8% positive over 6,193
labeled compounds (second most balanced endpoint after SR-ARE/SR-MMP) --
roughly midway on the imbalance spectrum between NR-PPAR-gamma and SR-MMP,
and a clean test of whether variance moves monotonically with class
scarcity across three points rather than being an artifact of only two.

Usage:
    uv run --group torch --group chem python run_third_endpoint.py
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

ENDPOINT = "NR-ER"
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

    def positive_count(rows) -> int:
        return sum(c.label for c in rows)

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
        "train_positive_count": positive_count(train),
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
        "train_positive_count": split_summary["train_positive_count"],
    }, indent=2))


if __name__ == "__main__":
    main()
