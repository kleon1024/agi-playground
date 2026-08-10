"""The descriptor-vs-model scoreboard, assembled from the recorded runs.

The mission's three endpoints each trained the descriptor baseline and the
SMILES model for three seeds. The mission README's scoreboard (descriptor
wins on SR-MMP, ties on NR-PPAR-gamma, loses on NR-ER) lives across the
stage records; this script assembles the per-endpoint mean and seed spread
from the recorded JSONs so the scoreboard is a table, not a summary.

Inputs (recorded, unchanged): the descriptor-seed*.json and model-seed*.json
under each endpoint stage's runs/.

Run:
    uv run python core/scoreboard.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

ENDPOINTS = (
    ("SR-MMP", "01-descriptor-baseline-and-model"),
    ("NR-PPAR-gamma", "03-second-endpoint"),
    ("NR-ER", "04-third-endpoint"),
)


def load_scores(root: Path, stage: str, prefix: str) -> list[float]:
    out = []
    for seed in (0, 1, 2):
        with open(root / stage / "runs" / f"{prefix}-seed{seed}.json") as fh:
            out.append(json.load(fh)["test_roc_auc"])
    return out


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    print(f"{'endpoint':<16} {'descriptor':>20} {'model':>20} {'margin':>9} {'winner':>12}")
    for name, stage in ENDPOINTS:
        desc = load_scores(root, stage, "descriptor")
        model = load_scores(root, stage, "model")
        d_mean, m_mean = statistics.fmean(desc), statistics.fmean(model)
        d_spread = (max(desc) - min(desc)) / 2
        m_spread = (max(model) - min(model)) / 2
        spread = max(d_spread, m_spread)
        margin = d_mean - m_mean
        verdict = (
            "descriptor" if margin > spread else
            "model" if -margin > spread else
            "inside spread"
        )
        print(
            f"{name:<16} {d_mean:>8.4f}±{d_spread:.4f} {m_mean:>8.4f}±{m_spread:.4f} "
            f"{margin:>+9.4f} {verdict:>12}"
        )


if __name__ == "__main__":
    main()
