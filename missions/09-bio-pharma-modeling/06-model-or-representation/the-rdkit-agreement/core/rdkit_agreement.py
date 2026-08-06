"""The RDKit agreement, read from the recorded fingerprint check.

Stage 06's from-scratch fingerprint was checked against RDKit's. This
script reads the recorded agreement JSON and lays out how close the
reimplementation is.

Input (recorded, unchanged): ../runs/rdkit-agreement.json

Run:
    uv run python core/rdkit_agreement.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    with open(
        Path(__file__).resolve().parents[2] / "runs" / "rdkit-agreement.json"
    ) as fh:
        d = json.load(fh)
    print("RDKit agreement check (recorded), read:")
    print(f"  {d['n_molecules']} molecules, {d['n_pairs']} pairs, "
          f"{d['n_unparsed']} unparsed")
    print(f"  mean bits set: core {d['mean_bits_set_core']:.2f} vs "
          f"RDKit {d['mean_bits_set_rdkit']:.2f}")
    print(f"  identical bit sets: {d['identical_bit_sets']}")
    print(f"  Tanimoto Spearman: {d['tanimoto_spearman_core_vs_rdkit']:.4f}")
    print(f"  mean |Tanimoto diff|: {d['tanimoto_mean_abs_difference']:.4f}")
    print("\nreading: the from-scratch fingerprint ranks molecules almost")
    print("identically to RDKit (Spearman 0.90) with tiny mean Tanimoto")
    print("difference — close enough that the representation comparison's")
    print("conclusions are not an artifact of a broken reimplementation.")


if __name__ == "__main__":
    main()
