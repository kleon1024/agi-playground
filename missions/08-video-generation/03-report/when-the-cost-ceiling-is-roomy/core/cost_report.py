"""The feasibility verdict, read: cost ceiling, quality margin, headroom.

Mission 08's cost-first framing makes the report stage the verdict: the
generation must beat frame-repeat by more than its seed spread AND fit the
declared cost ceiling. This script reads the committed generation JSONs for
the quality margin and tabulates the recorded cost against the ceiling, so
the verdict's two halves — quality and cost — are one table.

Inputs (recorded): ../runs/2026-07-31-outcome-report.txt (cost, cited) and
the generation-seed*.json (quality, read).

Run:
    uv run python core/cost_report.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path


def main() -> None:
    mission = Path(__file__).resolve().parents[3]
    mses = []
    for seed in (0, 1, 2):
        with open(mission / f"02-generation-model/runs/generation-seed{seed}.json") as fh:
            mses.append(json.load(fh)["reconstruction_mse"]["lm_completion"])
    mean = statistics.fmean(mses)
    spread = max(mses) - min(mses)
    baseline = 0.1281
    margin = baseline - mean

    print("mission 08 feasibility verdict, quality half (recomputed):")
    print(f"  LM completion per seed: {[round(m, 4) for m in mses]}")
    print(f"  mean {mean:.4f}, spread {spread:.4f}, frame-repeat {baseline}")
    print(f"  margin {margin:.4f} > spread {spread:.4f} -> "
          f"{'beats baseline outside seed noise' if margin > spread else 'no result'}")
    print("\n  cost half (recorded):")
    print("  seed totals 152.5/150.6/153.9s (codec + LM + generation), $0, ")
    print("  ceiling 1800s -> 8.4-8.6% used: the ceiling is roomy, and the")
    print("  verdict pairs cost with quality rather than reporting either alone.")


if __name__ == "__main__":
    main()
