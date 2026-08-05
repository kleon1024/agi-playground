"""The scarcity hypothesis, read from the cross-endpoint analysis.

Stage 05's recorded analysis put the three endpoints' positive counts,
model variance, and verdicts side by side and checked monotonicity. This
script reads the recorded JSON and lays out the two directions the stage
measured: model variance vs positive count, and the win/loss gap vs
positive count — so "scarcity drives variance" is a table, and the
non-monotonic gap is the part the hypothesis does not explain.

Input (recorded, unchanged): ../runs/2026-08-01-cross-endpoint-analysis.json

Run:
    uv run python core/scarcity_grid.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    with open(Path(__file__).resolve().parents[2] / "runs" / "2026-08-01-cross-endpoint-analysis.json") as fh:
        d = json.load(fh)
    print(f"{'endpoint':<14} {'train+':>7} {'model spread':>13} {'gap':>8} {'verdict':<26}")
    for e in d["endpoints"]:
        print(
            f"{e['name']:<14} {e['train_positive_count']:>7} {e['model_auc_spread']:>13.4f} "
            f"{e['gap_model_minus_descriptor']:>+8.4f} {e['verdict']:<26}"
        )
    print(f"\nvariance vs positive count: {d['variance_vs_positive_count_direction']}")
    print(f"gap vs positive count: {d['gap_vs_positive_count_direction']}")
    print(f"note: {d.get('note')}")


if __name__ == "__main__":
    main()
