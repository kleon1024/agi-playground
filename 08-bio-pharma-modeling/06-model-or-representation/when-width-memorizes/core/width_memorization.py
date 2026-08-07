"""When representation width buys memorization instead of generalization.

Stage 06's recorded grid includes a bit-width sweep on SR-MMP: the same
molecules, the same logistic learner, three fingerprint widths. This script
reads that recorded sweep plus the RDKit-agreement record and lays out the
one number that decides the story — the gap between train and test AUC, and
how it grows with width while test AUC does not.

Inputs (recorded, unchanged):
- ../representation-grid.json (the grid record's bit_width_sweep)
- ../rdkit-agreement.json (core fingerprint vs RDKit agreement)

Run:
    uv run python core/width_memorization.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[2] / "runs"
    with open(root / "representation-grid.json") as fh:
        grid = json.load(fh)
    with open(root / "rdkit-agreement.json") as fh:
        agreement = json.load(fh)

    print("bit-width sweep, SR-MMP (recorded 2026-08-05)")
    print(f"{'n_bits':>8} {'train AUC':>10} {'test AUC':>9} {'gap':>7} {'test spread':>12}")
    widths = grid["bit_width_sweep"]["widths"]
    for w in widths:
        gap = w["train_auc_mean"] - w["test_auc_mean"]
        print(
            f"{w['n_bits']:>8} {w['train_auc_mean']:>10.4f} {w['test_auc_mean']:>9.4f} "
            f"{gap:>7.4f} {w['test_auc_spread']:>12.4f}"
        )

    print("\nRDKit agreement (core fingerprint vs RDKit, n=60 molecules)")
    print(f"  mean bits set: core {agreement['mean_bits_set_core']:.2f} vs "
          f"rdkit {agreement['mean_bits_set_rdkit']:.2f}")
    print(f"  identical bit sets: {agreement['identical_bit_sets']}/{agreement['n_molecules']}")
    print(f"  tanimoto Spearman (core vs rdkit): {agreement['tanimoto_spearman_core_vs_rdkit']:.3f}")
    print(f"  mean |tanimoto difference|: {agreement['tanimoto_mean_abs_difference']:.4f}")

    print("\nverdicts (recorded):", grid["verdicts"])
    print("note:", grid["note"])


if __name__ == "__main__":
    main()
