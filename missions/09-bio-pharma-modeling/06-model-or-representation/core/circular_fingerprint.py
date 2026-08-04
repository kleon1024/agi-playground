"""A circular (ECFP-style) fingerprint, written out rather than called.

Stage 01's ten descriptors reduce a molecule to ten physicochemical numbers:
weight, LogP, polar surface area, ring counts, and so on. Every molecule with
the same weight, LogP, and ring count is the same point to that
representation, however differently its atoms are actually wired. A circular
fingerprint asks a different question -- not "how heavy and greasy is this
molecule" but "which local atomic neighbourhoods does it contain" -- and
answers it in a few thousand bits instead of ten floats.

The algorithm is Morgan's, as used by ECFP (Rogers & Hahn, 2010):

1. Give every atom an initial identifier from its own invariant properties:
   atomic number, heavy-atom degree, formal charge, attached hydrogens,
   ring membership, aromaticity. Two atoms start identical exactly when
   those six agree.
2. Repeat `radius` times: replace each atom's identifier with a hash of its
   current identifier together with the sorted (bond order, neighbour
   identifier) pairs around it. After iteration k an identifier summarizes
   everything within k bonds of that atom.
3. Every identifier produced at every iteration -- not only the last -- is a
   substructure the molecule contains. Fold them into `n_bits` by taking the
   identifier modulo the width, and set those bits.

Step 3's folding is where information is deliberately thrown away: two
unrelated substructures can land on the same bit, and at 2048 bits over a
few thousand molecules that will happen. The fingerprint is a lossy
membership test, not a description you can invert.

RDKit is used here only to parse SMILES into an atom-and-bond graph, the
same way stage 01 uses it to read a molecule before computing descriptors.
The hashing, the iteration, and the folding are this file's own; `prod/`
holds the two-line RDKit call that replaces all of it, and measures how
closely the two agree.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

RADIUS = 2  # ECFP4 in the usual naming: diameter 4 = radius 2
N_BITS = 2048


def _atom_invariants(atom) -> tuple:
    """The six properties two atoms must share to start out identical."""
    return (
        atom.GetAtomicNum(),
        atom.GetDegree(),
        atom.GetFormalCharge(),
        atom.GetTotalNumHs(),
        int(atom.IsInRing()),
        int(atom.GetIsAromatic()),
    )


def _stable_hash(value: tuple) -> int:
    """Python's `hash` is salted per process, which would make a fingerprint
    depend on which interpreter computed it. This is not that."""
    import hashlib

    return int.from_bytes(
        hashlib.sha256(repr(value).encode()).digest()[:8], "big", signed=False
    )


def fingerprint_bits(smiles: str, radius: int = RADIUS, n_bits: int = N_BITS) -> set[int] | None:
    """The set bits for one molecule, or None if the SMILES will not parse."""
    from rdkit import Chem, RDLogger

    RDLogger.DisableLog("rdApp.*")
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    identifiers = {a.GetIdx(): _stable_hash(_atom_invariants(a)) for a in mol.GetAtoms()}
    bits = {identifiers[i] % n_bits for i in identifiers}

    for _ in range(radius):
        updated = {}
        for atom in mol.GetAtoms():
            idx = atom.GetIdx()
            neighbours = sorted(
                (
                    mol.GetBondBetweenAtoms(idx, nbr.GetIdx()).GetBondTypeAsDouble(),
                    identifiers[nbr.GetIdx()],
                )
                for nbr in atom.GetNeighbors()
            )
            updated[idx] = _stable_hash((identifiers[idx], tuple(neighbours)))
        identifiers = updated
        bits |= {identifiers[i] % n_bits for i in identifiers}

    return bits


def fingerprint_vector(smiles: str, radius: int = RADIUS, n_bits: int = N_BITS) -> np.ndarray | None:
    bits = fingerprint_bits(smiles, radius, n_bits)
    if bits is None:
        return None
    vec = np.zeros(n_bits, dtype=np.float64)
    vec[list(bits)] = 1.0
    return vec


def load_fingerprint_matrix(
    csv_path: Path, radius: int = RADIUS, n_bits: int = N_BITS
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Same contract as stage 01's `load_descriptor_matrix`: returns
    (X, y, dropped_mol_ids), dropping and reporting rows that fail to parse
    rather than silently skipping them."""
    rows_x, rows_y, dropped = [], [], []
    with Path(csv_path).open() as f:
        for row in csv.DictReader(f):
            vec = fingerprint_vector(row["smiles"], radius, n_bits)
            if vec is None:
                dropped.append(row["mol_id"])
                continue
            rows_x.append(vec)
            rows_y.append(int(row["label"]))
    return np.array(rows_x, dtype=np.float64), np.array(rows_y, dtype=np.int64), dropped


def tanimoto(a: set[int], b: set[int]) -> float:
    """Shared bits over total distinct bits -- the standard similarity for
    binary fingerprints, and the thing `prod/` compares against RDKit."""
    union = len(a | b)
    return len(a & b) / union if union else 0.0


def density_report(X: np.ndarray) -> dict:
    """How much of the 2048-bit space this corpus actually occupies. A
    fingerprint matrix that is almost entirely zero is telling you the width
    is doing nothing for these molecules."""
    per_molecule = X.sum(axis=1)
    columns_used = int((X.sum(axis=0) > 0).sum())
    return {
        "n_bits": X.shape[1],
        "mean_bits_set_per_molecule": float(per_molecule.mean()),
        "min_bits_set": int(per_molecule.min()),
        "max_bits_set": int(per_molecule.max()),
        "columns_ever_set": columns_used,
        "columns_ever_set_fraction": columns_used / X.shape[1],
        "matrix_density": float(X.mean()),
    }
