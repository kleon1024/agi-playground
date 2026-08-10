"""The n=3 directional read, from the recorded cross-endpoint analysis.

Stage 05's three-endpoint pattern has a stated ceiling: the monotonicity
is n=3 and directional, not a fitted claim. This script reads the recorded
JSON and lays out the two directions and the honest boundary.

Input (recorded, unchanged): ../runs/2026-08-01-cross-endpoint-analysis.json

Run:
    uv run python core/directional_read.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    with open(
        Path(__file__).resolve().parents[2]
        / "runs"
        / "2026-08-01-cross-endpoint-analysis.json"
    ) as fh:
        d = json.load(fh)
    print("cross-endpoint analysis (recorded), read:")
    for e in d["endpoints"]:
        print(f"  {e['name']:<14} train+ {e['train_positive_count']:>4} "
              f"model spread {e['model_auc_spread']:.4f} "
              f"gap {e['gap_model_minus_descriptor']:+.4f} "
              f"-> {e['verdict']}")
    print(f"\n  variance vs positives: {d['variance_vs_positive_count_direction']}")
    print(f"  gap vs positives: {d['gap_vs_positive_count_direction']}")
    print("\nreading: scarcity decides where a winner can be seen (variance")
    print("monotonic up as positives shrink), not who wins (gap not")
    print("monotonic) — and the pattern is n=3 and directional, which the")
    print("analysis states as its ceiling.")


if __name__ == "__main__":
    main()
