"""The silence local minimum, read from the recorded codec training run.

Stage 00's first training attempt collapsed to a silence-matching local
minimum: recon MSE 0.325, codebook usage 1-2 of 64. This script reads the
record and lays out what the pilot showed and how the escape worked.

Input (recorded, unchanged): ../runs/2026-07-31-codec-training.md

Run:
    uv run python core/silence_minimum.py
"""

from __future__ import annotations

import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2] / "runs" / "2026-07-31-codec-training.md"
    ).read_text()
    print("the silence local minimum (recorded), read:")
    for row in re.findall(
        r"(plateaued at recon MSE [\d.]+|"
        r"codebook usage collapsed to [\d-]+ of \d+ codes|"
        r"outputting near-silence is a locally optimal way[^\n]*|"
        r"loss drops sharply \([\d.]+ -> [\d.]+ over[^\n]*)", run
    ):
        print(f"  {row.strip()}")
    print("\nreading: against a zero-mean signal, silence is locally optimal —")
    print("the decoder must escape a genuine minimum, and the escape is why")
    print("the training recipe (higher LR, longer) matters as much as the loss.")


if __name__ == "__main__":
    main()
