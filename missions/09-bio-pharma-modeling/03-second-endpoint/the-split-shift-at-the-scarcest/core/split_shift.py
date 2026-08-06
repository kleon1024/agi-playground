"""The split shift at the scarcest endpoint, read from the recorded seeds.

Stage 03's NR-PPAR-gamma split shifts the positive rate sharply (2.29%
train vs 5.28% test) — the largest shift in the panel, on the scarcest
endpoint. This script reads the recorded split summary and lays out the
shift beside the verdict.

Input (recorded, unchanged): ../data/split_summary.json

Run:
    uv run python core/split_shift.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    with open(
        Path(__file__).resolve().parents[2] / "data" / "split_summary.json"
    ) as fh:
        d = json.load(fh)
    print("NR-PPAR-gamma split (recorded), read:")
    ss = d.get("scaffold_split_stats", {})
    print(f"  n_train {d.get('n_train')} n_test {d.get('n_test')}, "
          f"scaffold overlap {ss.get('overlap_scaffold_count')}")
    tr = d.get("train_positive_rate")
    te = d.get("test_positive_rate")
    if tr is not None and te is not None:
        print(f"  train positive {tr*100:.2f}% vs test {te*100:.2f}% "
              f"(shift {te/tr:.1f}x)")
    print("\nreading: the scarcest endpoint carries the largest split shift —")
    print("with 118 train positives, whole-scaffold assignment moves a larger")
    print("fraction of the minority class, which is the same confound the")
    print("inconclusive verdict's variance measures.")


if __name__ == "__main__":
    main()
