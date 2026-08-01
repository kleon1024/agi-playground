"""Standard RDKit descriptors: the field's usual first fixed feature set for
a molecule, computed with no learning involved.

Ten descriptors, chosen because each is a commonly cited fixed
structural/physicochemical property (`mission.yaml`'s own list: "molecular
weight, LogP, TPSA, ring counts, and similar"), not a hand-picked set tuned
to this endpoint after seeing results.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

DESCRIPTOR_NAMES = [
    "MolWt", "MolLogP", "TPSA", "NumHDonors", "NumHAcceptors",
    "NumRotatableBonds", "RingCount", "NumAromaticRings",
    "FractionCSP3", "NumHeteroatoms",
]


def compute_descriptors(smiles: str) -> list[float] | None:
    from rdkit import Chem, RDLogger
    from rdkit.Chem import Descriptors, Lipinski

    RDLogger.DisableLog("rdApp.*")
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return [
        Descriptors.MolWt(mol),
        Descriptors.MolLogP(mol),
        Descriptors.TPSA(mol),
        Lipinski.NumHDonors(mol),
        Lipinski.NumHAcceptors(mol),
        Lipinski.NumRotatableBonds(mol),
        Lipinski.RingCount(mol),
        Lipinski.NumAromaticRings(mol),
        Descriptors.FractionCSP3(mol),
        Lipinski.NumHeteroatoms(mol),
    ]


def load_descriptor_matrix(csv_path: Path) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Returns (X, y, dropped_mol_ids). Rows that fail to parse are dropped
    and their mol_ids reported, matching stage 00's own drop-and-report rule.
    """
    rows_x, rows_y, dropped = [], [], []
    with Path(csv_path).open() as f:
        for row in csv.DictReader(f):
            feats = compute_descriptors(row["smiles"])
            if feats is None:
                dropped.append(row["mol_id"])
                continue
            rows_x.append(feats)
            rows_y.append(int(row["label"]))
    return np.array(rows_x, dtype=np.float64), np.array(rows_y, dtype=np.int64), dropped
