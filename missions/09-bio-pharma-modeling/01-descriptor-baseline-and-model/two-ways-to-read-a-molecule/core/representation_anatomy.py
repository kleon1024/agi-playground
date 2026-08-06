"""Two ways to read a molecule: descriptor vs SMILES character model.

The bio-pharma "model" is actually two representations of the same
molecule, and the mission's finding lives in their difference. The
descriptor baseline maps each molecule to ten physicochemical numbers and
fits a convex logistic regression; the trained model maps the SMILES string
to characters and runs a 696K-parameter transformer. This script reads the
recorded runs and lays out the two structures side by side.

Inputs (recorded, unchanged): ../runs/descriptor-seed*.json and
model-seed*.json

Run:
    uv run python core/representation_anatomy.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path


def main() -> None:
    runs = Path(__file__).resolve().parents[2] / "runs"
    desc = [
        json.loads((runs / f"descriptor-seed{s}.json").read_text())["test_roc_auc"]
        for s in (0, 1, 2)
    ]
    model = [
        json.loads((runs / f"model-seed{s}.json").read_text())["test_roc_auc"]
        for s in (0, 1, 2)
    ]
    m0 = json.loads((runs / "model-seed0.json").read_text())
    print("two representations of one molecule, read from the recorded runs:")
    print("  descriptor:  10 RDKit numbers -> logistic regression")
    print(f"               mean ROC-AUC {statistics.fmean(desc):.4f}, "
          f"spread {max(desc)-min(desc):.4f}, ~2s/seed")
    print(f"  SMILES model: character transformer, {m0['n_params']:,} params, "
          f"vocab {m0['vocab_size']}")
    print(f"               mean ROC-AUC {statistics.fmean(model):.4f}, "
          f"spread {max(model)-min(model):.4f}, ~105s/seed")
    print("\nreading: the descriptor's edge on SR-MMP is partly that it is a")
    print("stable, cheap ten-number summary; the transformer's variance is")
    print("where the mission's scarcity story begins.")


if __name__ == "__main__":
    main()
