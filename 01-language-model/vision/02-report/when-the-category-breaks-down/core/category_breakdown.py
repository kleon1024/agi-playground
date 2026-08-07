"""The synthetic-set verdict's category structure, read.

Mission 05's report returned NOT MET (hosted API dominates) and recorded a
category breakdown of where each arm wins. This script reads the recorded
breakdown JSON and lays out the shape: the vision pathway's separation from
text-only concentrates on the leak-proof type, while the hosted API
dominates everywhere — which is why the aggregate verdict hides where the
pathway's signal is real.

Input (recorded, unchanged): ../runs/category-breakdown.json

Run:
    uv run python core/category_breakdown.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    with open(Path(__file__).resolve().parents[2] / "runs" / "category-breakdown.json") as fh:
        d = json.load(fh)
    by_cat = d["by_category"]
    cats = sorted(by_cat["vision"])
    print("synthetic-set category breakdown (recorded):")
    print(f"  {'category':<14} {'vision':>8} {'text-only':>10} {'margin':>8}")
    for cat in cats:
        v = by_cat["vision"][cat]
        t = by_cat["text_only"][cat]
        v_acc = v["correct"] / v["total"]
        t_acc = t["correct"] / t["total"]
        print(f"  {cat:<14} {v_acc:>8.3f} {t_acc:>10.3f} {v_acc - t_acc:>+8.3f}")
    print("\nreading: vision separates from text-only where the question cannot")
    print("leak (shape_color), and the hosted API dominates both everywhere.")


if __name__ == "__main__":
    main()
