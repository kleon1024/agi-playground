"""The scaffold split's label shift, across the three endpoints.

The mission's scaffold split groups by Murcko core before splitting, so no
scaffold appears on both sides (checked, per the stage 00 run record: 1,668
scaffolds, 507 train scaffolds, zero overlap). But splitting by scaffold can
still shift the label distribution between train and test, because scaffolds
cluster by activity. This script reads the three recorded split summaries
and lays out that shift — the test positive rate minus the train's — beside
the descriptor-vs-model verdicts the mission recorded, so the question
"does the split decide who wins" has the numbers to answer it.

Inputs (recorded, unchanged):
- ../data/split_summary.json (three endpoint directories)

Run:
    uv run python core/split_diagnostics.py
"""

from __future__ import annotations

import json
from pathlib import Path

ENDPOINTS = (
    ("SR-MMP", "00-dataset-and-property", "descriptor wins beyond spread"),
    ("NR-PPAR-gamma", "03-second-endpoint", "inconclusive (gap inside spread)"),
    ("NR-ER", "04-third-endpoint", "descriptor wins beyond spread"),
)


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    print(f"{'endpoint':<16} {'train+':>7} {'test+':>7} {'shift pp':>9} {'verdict':<30}")
    for name, rel, verdict in ENDPOINTS:
        with open(root / rel / "data" / "split_summary.json") as fh:
            s = json.load(fh)
        shift = (s["test_positive_rate"] - s["train_positive_rate"]) * 100
        print(
            f"{name:<16} {s['train_positive_rate']*100:>6.1f}% {s['test_positive_rate']*100:>6.1f}% "
            f"{shift:>+8.1f}pp  {verdict}"
        )


if __name__ == "__main__":
    main()
