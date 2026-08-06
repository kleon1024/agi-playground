"""The variance that decides, read from the report's own rule.

Stage 09's report is built on the rule that a candidate must beat each
baseline by more than its 95% uncertainty margin, across at least five
seeds. The breached fixture is the case where the headline gap clears the
margin and a guardrail still vetoes. This script reads the fixture's
seed-level arrays and lays out the variance math the verdict depends on.

Input (recorded, unchanged): ../core/fixtures/breached.json

Run:
    uv run python core/variance_read.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path


def main() -> None:
    with open(
        Path(__file__).resolve().parents[2] / "core" / "fixtures" / "breached.json"
    ) as fh:
        d = json.load(fh)
    cand = d["primary_metric"]["candidate"]
    pop = d["primary_metric"]["baselines"]["popularity"]
    cf = d["primary_metric"]["baselines"]["item_item_cf"]
    print("the variance that decides (breached fixture), read:")
    print(f"  candidate nDCG@10 per seed: {[round(x,4) for x in cand]}")
    print(f"  popularity per seed:        {[round(x,4) for x in pop]}")
    print(f"  item-item CF per seed:      {[round(x,4) for x in cf]}")
    print(f"  candidate spread: {max(cand)-min(cand):.4f} vs gap to CF "
          f"{statistics.fmean(cand)-statistics.fmean(cf):.4f}")
    print("\nreading: the report rejects a positive mean gap not larger than its")
    print("95% margin — and still renders NOT MET when the cold-start guardrail")
    print("falls below its baseline. Variance is a veto input, not an appendix.")


if __name__ == "__main__":
    main()
