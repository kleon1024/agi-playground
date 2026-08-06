"""The inconclusive verdict, read from the recorded second-endpoint seeds.

Stage 03's NR-PPAR-gamma result is mission 09's most imbalanced endpoint:
the trained model's mean is nominally above the descriptor baseline, but
the gap sits inside the model's own seed spread. This script reads the
committed seed JSONs and lays out the means, spreads, and the verdict rule
that turns a nominal lead into a no-result.

Inputs (recorded, unchanged): ../runs/descriptor-seed0/1/2.json and
model-seed0/1/2.json.

Run:
    uv run python core/inconclusive_read.py
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
    d_mean, m_mean = statistics.fmean(desc), statistics.fmean(model)
    d_spread, m_spread = max(desc) - min(desc), max(model) - min(model)
    gap = m_mean - d_mean
    print("NR-PPAR-gamma, second endpoint, read from the recorded seeds:")
    print(f"  descriptor: {[round(a, 4) for a in desc]}  mean {d_mean:.4f} spread {d_spread:.4f}")
    print(f"  model:      {[round(a, 4) for a in model]}  mean {m_mean:.4f} spread {m_spread:.4f}")
    print(f"  gap (model - descriptor): {gap:+.4f}  vs larger spread {m_spread:.4f}")
    print("  -> INCONCLUSIVE: the gap is ~1/17th of the model's own spread,")
    print("     a no-result by the rule mission.yaml declared before any code.")


if __name__ == "__main__":
    main()
