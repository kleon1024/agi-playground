"""The model's first clean win, read from the recorded third-endpoint seeds.

Stage 04's NR-ER result is the trained model's first win beyond spread.
This script reads the recorded seed JSONs and lays out the margin and the
spread.

Inputs (recorded, unchanged): ../runs/descriptor-seed*.json and
model-seed*.json

Run:
    uv run python core/model_win.py
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
    print("NR-ER (recorded), read:")
    print(f"  descriptor {[round(x,4) for x in desc]} mean "
          f"{statistics.fmean(desc):.4f} spread {max(desc)-min(desc):.4f}")
    print(f"  model      {[round(x,4) for x in model]} mean "
          f"{statistics.fmean(model):.4f} spread {max(model)-min(model):.4f}")
    print(f"  margin {statistics.fmean(model)-statistics.fmean(desc):+.4f} "
          f"vs larger spread {max(max(model)-min(model), max(desc)-min(desc)):.4f}")
    print("\nreading: the model wins beyond its own spread on the mid-range")
    print("endpoint — the first model win in the mission, and the third point")
    print("that separates the scarcity-variance pattern from who wins.")


if __name__ == "__main__":
    main()
