"""Download Tox21, pick one endpoint, and build a Murcko-scaffold split.

`mission.yaml` requires the split to group by scaffold rather than shuffle
randomly, and to *measure* the resulting train/test scaffold overlap rather
than assume a scaffold split makes it zero. This script does both: it groups
every labeled compound by its Murcko scaffold (the ring system with
substituents stripped, via RDKit), assigns whole scaffold groups to train or
test so no scaffold can appear on both sides by construction, and then checks
that directly on the output rather than trusting the construction.

One real wrinkle the check surfaces: a molecule with no rings at all (a plain
chain) has an *empty* Murcko scaffold (`""`). Every acyclic molecule in the
dataset therefore collides into the same scaffold group, which is reported
explicitly rather than silently split apart or silently kept whole.

Usage:
    python prepare_dataset.py --endpoint SR-MMP --train-frac 0.8 --split-seed 0 \
        --url https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/tox21.csv.gz \
        --out ../data
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import random
import time
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

ALL_ENDPOINTS = [
    "NR-AR", "NR-AR-LBD", "NR-AhR", "NR-Aromatase", "NR-ER", "NR-ER-LBD",
    "NR-PPAR-gamma", "SR-ARE", "SR-ATAD5", "SR-HSE", "SR-MMP", "SR-p53",
]


def download(url: str, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    csv_path = dest / "tox21.csv"
    if csv_path.exists():
        return csv_path
    with urllib.request.urlopen(url, timeout=60) as resp:
        raw = resp.read()
    text = gzip.decompress(raw).decode("utf-8")
    csv_path.write_text(text)
    return csv_path


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def label_stats(csv_path: Path) -> dict:
    """All 12 endpoints' labeled/positive counts, for the pre-registration
    record of why one endpoint was picked over the other 11."""
    counts = {e: {"labeled": 0, "positive": 0} for e in ALL_ENDPOINTS}
    with csv_path.open() as f:
        for row in csv.DictReader(f):
            for e in ALL_ENDPOINTS:
                v = row[e]
                if v in ("0", "1"):
                    counts[e]["labeled"] += 1
                    counts[e]["positive"] += int(v)
    for e, value in counts.items():
        labeled = value["labeled"]
        value["positive_rate"] = value["positive"] / labeled if labeled else 0.0
    return counts


@dataclass
class Compound:
    mol_id: str
    smiles: str
    label: int


def load_endpoint(csv_path: Path, endpoint: str) -> list[Compound]:
    rows = []
    with csv_path.open() as f:
        for row in csv.DictReader(f):
            v = row[endpoint]
            if v in ("0", "1"):
                rows.append(Compound(row["mol_id"], row["smiles"], int(v)))
    return rows


def murcko_scaffolds(compounds: list[Compound]) -> tuple[dict[str, str], list[str]]:
    """Return {mol_id: scaffold_smiles} and the mol_ids RDKit could not parse."""
    from rdkit import Chem, RDLogger
    from rdkit.Chem.Scaffolds import MurckoScaffold

    RDLogger.DisableLog("rdApp.*")
    scaffolds: dict[str, str] = {}
    dropped: list[str] = []
    for c in compounds:
        mol = Chem.MolFromSmiles(c.smiles)
        if mol is None:
            dropped.append(c.mol_id)
            continue
        scaffolds[c.mol_id] = MurckoScaffold.MurckoScaffoldSmiles(mol=mol)
    return scaffolds, dropped


def scaffold_split(
    compounds: list[Compound], scaffolds: dict[str, str], train_frac: float, seed: int
) -> tuple[list[Compound], list[Compound], dict]:
    groups: dict[str, list[Compound]] = defaultdict(list)
    for c in compounds:
        if c.mol_id in scaffolds:
            groups[scaffolds[c.mol_id]].append(c)

    group_items = list(groups.items())
    rng = random.Random(seed)
    rng.shuffle(group_items)
    # Stable sort by descending size: the seed only breaks ties among
    # equal-size groups, so the split is reproducible for a fixed seed and
    # large scaffold groups still anchor whichever side gets them first.
    group_items.sort(key=lambda kv: len(kv[1]), reverse=True)

    n_total = sum(len(v) for _, v in group_items)
    target_train = round(train_frac * n_total)

    train: list[Compound] = []
    test: list[Compound] = []
    train_scaffolds: set[str] = set()
    test_scaffolds: set[str] = set()
    empty_scaffold_side = None
    for scaffold, members in group_items:
        if scaffold == "":
            empty_scaffold_side = "train" if len(train) < target_train else "test"
        if len(train) < target_train:
            train.extend(members)
            train_scaffolds.add(scaffold)
        else:
            test.extend(members)
            test_scaffolds.add(scaffold)

    overlap_scaffolds = train_scaffolds & test_scaffolds
    overlap_test_molecules = sum(
        1 for c in test if scaffolds.get(c.mol_id) in overlap_scaffolds
    )
    stats = {
        "n_scaffold_groups": len(group_items),
        "n_train": len(train),
        "n_test": len(test),
        "n_train_scaffolds": len(train_scaffolds),
        "n_test_scaffolds": len(test_scaffolds),
        "overlap_scaffold_count": len(overlap_scaffolds),
        "overlap_test_molecule_fraction": overlap_test_molecules / len(test) if test else 0.0,
        "empty_scaffold_group_size": len(groups.get("", [])),
        "empty_scaffold_assigned_to": empty_scaffold_side,
    }
    return train, test, stats


def write_split(path: Path, rows: list[Compound], scaffolds: dict[str, str]) -> None:
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["mol_id", "smiles", "label", "scaffold"])
        for c in rows:
            w.writerow([c.mol_id, c.smiles, c.label, scaffolds.get(c.mol_id, "")])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", default="SR-MMP", choices=ALL_ENDPOINTS)
    ap.add_argument(
        "--url",
        default="https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/tox21.csv.gz",
    )
    ap.add_argument("--train-frac", type=float, default=0.8)
    ap.add_argument("--split-seed", type=int, default=0)
    ap.add_argument("--out", default="../data")
    args = ap.parse_args()

    out = Path(args.out)
    t0 = time.time()
    csv_path = download(args.url, out / "raw")
    dataset_hash = sha256_of(csv_path)

    all_stats = label_stats(csv_path)
    compounds = load_endpoint(csv_path, args.endpoint)
    scaffolds, dropped = murcko_scaffolds(compounds)
    kept = [c for c in compounds if c.mol_id in scaffolds]

    train, test, split_stats = scaffold_split(kept, scaffolds, args.train_frac, args.split_seed)
    write_split(out / "train.csv", train, scaffolds)
    write_split(out / "test.csv", test, scaffolds)

    def positive_rate(rows: list[Compound]) -> float:
        return sum(c.label for c in rows) / len(rows) if rows else 0.0

    summary = {
        "endpoint": args.endpoint,
        "url": args.url,
        "dataset_sha256": dataset_hash,
        "n_total_rows_in_file": sum(1 for _ in csv.DictReader(csv_path.open())),
        "n_labeled_for_endpoint": len(compounds),
        "n_dropped_unparseable_smiles": len(dropped),
        "dropped_mol_ids": dropped,
        "all_endpoint_label_stats": all_stats,
        "train_frac_target": args.train_frac,
        "split_seed": args.split_seed,
        "n_train": len(train),
        "n_test": len(test),
        "train_positive_rate": positive_rate(train),
        "test_positive_rate": positive_rate(test),
        "scaffold_split_stats": split_stats,
        "wall_clock_seconds": time.time() - t0,
    }
    (out / "split_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
