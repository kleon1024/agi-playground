"""The recipe that broke then fixed on real speech, read from the record.

Stage 03's real-speech retrain found the synthetic recipe collapses on
LibriSpeech at 600 steps and escapes at 2000 — and a higher LR never
escapes at all. This script reads the recorded sweep and the production
seeds.

Inputs (recorded, unchanged): ../runs/2026-08-01-real-speech-and-network.md
and real-speech-seed*.json

Run:
    uv run python core/recipe_read.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path


def main() -> None:
    run = (
        Path(__file__).resolve().parents[2]
        / "runs"
        / "2026-08-01-real-speech-and-network.md"
    ).read_text()
    print("real-speech codec recipe (recorded), read:")
    for row in re.findall(
        r"(lr=1e-3 \(unchanged\):[^\n]*|lr=3e-3 \(higher\):\s*[^\n]*)", run
    ):
        print(f"  {row}")
    runs = Path(__file__).resolve().parents[2] / "runs"
    for seed in (0, 1, 2):
        with open(runs / f"real-speech-seed{seed}.json") as fh:
            d = json.load(fh)
        usage = d.get("codebook_usage", {})
        print(f"  seed {seed}: eval MSE {d.get('codec_eval_mse', 0):.5f}, "
              f"codes {usage.get('unique_codes_used')}/"
              f"{usage.get('codebook_size')}")
    print("\nreading: the same LR that escaped synthetic tones collapses on")
    print("real speech at 600 steps and escapes by 2000; a higher LR never")
    print("escapes — the recipe's escape window is input-dependent, which is")
    print("why the production run fixed the step count.")


if __name__ == "__main__":
    main()
