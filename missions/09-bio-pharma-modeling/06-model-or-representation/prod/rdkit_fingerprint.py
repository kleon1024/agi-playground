"""The same fingerprint in two lines, and an honest measure of the gap.

`core/circular_fingerprint.py` is about a hundred lines. In production it is
this:

    from rdkit.Chem import rdFingerprintGenerator
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    bits = gen.GetFingerprint(mol)

The two will not agree bit for bit and cannot: RDKit hashes atom
environments with its own function, so the same substructure lands on a
different bit index. Claiming agreement at the bit level would be a claim
about hash collisions, not about chemistry.

What *can* be compared is the thing a fingerprint is used for. Both are
consumed through Tanimoto similarity -- shared bits over total bits -- so
the test that matters is whether the two implementations rank molecule pairs
the same way. This script computes every pairwise Tanimoto over a sample of
molecules under both implementations and reports Spearman rank correlation
between the two similarity lists, plus the mean absolute difference.

Usage:
    uv run --group chem python rdkit_fingerprint.py --sample 120
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

CORE = Path(__file__).resolve().parent.parent / "core"
sys.path.insert(0, str(CORE))
from circular_fingerprint import N_BITS, RADIUS, fingerprint_bits, tanimoto


def rdkit_bits(smiles: str, radius: int = RADIUS, n_bits: int = N_BITS) -> set[int] | None:
    from rdkit import Chem, RDLogger
    from rdkit.Chem import rdFingerprintGenerator

    RDLogger.DisableLog("rdApp.*")
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=radius, fpSize=n_bits)
    return set(gen.GetFingerprint(mol).GetOnBits())


def spearman(a: list[float], b: list[float]) -> float:
    """Rank correlation, computed here rather than imported, so this file has
    the same from-scratch-where-it-teaches property as the rest of the repo.
    Ties get average ranks."""

    def ranks(xs: list[float]) -> np.ndarray:
        order = np.argsort(xs, kind="stable")
        r = np.empty(len(xs), dtype=np.float64)
        r[order] = np.arange(len(xs), dtype=np.float64)
        # average tied ranks
        values = np.asarray(xs, dtype=np.float64)[order]
        i = 0
        while i < len(values):
            j = i
            while j + 1 < len(values) and values[j + 1] == values[i]:
                j += 1
            if j > i:
                r[order[i : j + 1]] = np.arange(i, j + 1).mean()
            i = j + 1
        return r

    ra, rb = ranks(a), ranks(b)
    ra = ra - ra.mean()
    rb = rb - rb.mean()
    denom = float(np.sqrt((ra**2).sum() * (rb**2).sum()))
    return float((ra * rb).sum() / denom) if denom else 0.0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--csv",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "00-dataset-and-property" / "data" / "test.csv",
    )
    ap.add_argument("--sample", type=int, default=120)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "runs" / "rdkit-agreement.json")
    args = ap.parse_args()

    with args.csv.open() as f:
        rows = list(csv.DictReader(f))[: args.sample]

    t0 = time.perf_counter()
    mine, theirs, unparsed = [], [], []
    for row in rows:
        a, b = fingerprint_bits(row["smiles"]), rdkit_bits(row["smiles"])
        if a is None or b is None:
            unparsed.append(row["mol_id"])
            continue
        mine.append(a)
        theirs.append(b)

    my_sims, their_sims = [], []
    for i in range(len(mine)):
        for j in range(i + 1, len(mine)):
            my_sims.append(tanimoto(mine[i], mine[j]))
            their_sims.append(tanimoto(theirs[i], theirs[j]))

    diffs = np.abs(np.array(my_sims) - np.array(their_sims))
    result = {
        "csv": str(args.csv.name),
        "n_molecules": len(mine),
        "n_unparsed": len(unparsed),
        "n_pairs": len(my_sims),
        "radius": RADIUS,
        "n_bits": N_BITS,
        "mean_bits_set_core": float(np.mean([len(s) for s in mine])),
        "mean_bits_set_rdkit": float(np.mean([len(s) for s in theirs])),
        "identical_bit_sets": sum(1 for a, b in zip(mine, theirs) if a == b),
        "tanimoto_spearman_core_vs_rdkit": spearman(my_sims, their_sims),
        "tanimoto_mean_abs_difference": float(diffs.mean()),
        "tanimoto_max_abs_difference": float(diffs.max()),
        "wall_clock_s": time.perf_counter() - t0,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
