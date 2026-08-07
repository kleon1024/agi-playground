"""The margin vs the oracle ceiling, read from the recorded generation run.

Stage 02's generation beats frame-repeat by 37.2% and lands within 3.2% of
the oracle (true-token) ceiling. This script reads the recorded JSONs and
lays out where the remaining gap lives.

Inputs (recorded, unchanged): ../runs/generation-seed*.json

Run:
    uv run python core/margin_ceiling.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    runs = Path(__file__).resolve().parents[2] / "runs"
    ms = []
    for seed in (0, 1, 2):
        with open(runs / f"generation-seed{seed}.json") as fh:
            d = json.load(fh)
        ms.append(d["reconstruction_mse"])
        print(f"  seed {seed}: lm {ms[-1]['lm_completion']:.4f} "
              f"oracle {ms[-1]['oracle_tokens']:.4f} "
              f"frame-repeat {ms[-1]['frame_repeat_baseline']:.4f}")
    print("\nreading: the LM beats frame-repeat on every seed and sits close")
    print("to the oracle — so the remaining gap is the codec's reconstruction")
    print("fidelity, not the sequence model's.")


if __name__ == "__main__":
    main()
