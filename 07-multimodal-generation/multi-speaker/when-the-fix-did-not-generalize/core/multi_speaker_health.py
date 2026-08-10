"""Codebook health at 10 speakers: the fix that did not generalize.

Stage 04 retrains the codec at 10 speakers, where the stage-03 fix was
supposed to carry. This script reads the three recorded seeds'
final codebook usage and reconstruction MSE and lays out the seed-dependent
health the stage found — the same seed-dependence the codebook chapters
measured on stage 03's narrow baseline, now at the frontier.

Inputs (recorded, unchanged): ../runs/multi-speaker-seed{0,1,2}.json

Run:
    uv run python core/multi_speaker_health.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[2] / "runs"
    print(f"{'seed':>4} {'codes':>6} {'entropy':>8} {'MSE':>8}")
    for seed in (0, 1, 2):
        with open(root / f"multi-speaker-seed{seed}.json") as fh:
            d = json.load(fh)
        u = d["codebook_usage"]
        print(
            f"{seed:>4} {u['unique_codes_used']:>4}/{u['codebook_size']:<2} "
            f"{u['entropy_ratio']:>8.3f} {d['codec_eval_mse']:>8.4f}"
        )


if __name__ == "__main__":
    main()
