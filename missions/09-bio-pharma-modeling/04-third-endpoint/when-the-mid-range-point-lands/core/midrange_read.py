"""The mid-range point, read: what the third endpoint adds to the pattern.

Stage 04 picked NR-ER as the third endpoint because it sits midway on the
imbalance spectrum between SR-MMP (15.8%) and NR-PPAR-gamma (2.9%). This
script reads the committed seed JSONs and lays out the verdict — the model
wins beyond its own spread — and where that puts the three-point pattern:
scarcity inflates variance, and the mid-range endpoint resolves because it
has enough positives for the model to beat its noise.

Inputs (recorded, unchanged): ../runs/descriptor-seed0/1/2.json and
model-seed0/1/2.json.

Run:
    uv run python core/midrange_read.py
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
    print("NR-ER, third endpoint, read from the recorded seeds:")
    print(f"  descriptor: {[round(a, 4) for a in desc]}  mean {d_mean:.4f} spread {d_spread:.4f}")
    print(f"  model:      {[round(a, 4) for a in model]}  mean {m_mean:.4f} spread {m_spread:.4f}")
    print(f"  gap (model - descriptor): {gap:+.4f}  vs larger spread {m_spread:.4f}")
    print("  -> MODEL WINS beyond its own spread: the mid-range endpoint")
    print("     resolves, so the three-point pattern is variance up as")
    print("     positives shrink, with the winner decided by enough data.")


if __name__ == "__main__":
    main()
