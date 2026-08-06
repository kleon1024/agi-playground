"""The seed-dependent codebook health, read from the recorded multi-speaker run.

Stage 04's 10-speaker retrain showed no full collapse, but codebook health
became seed-dependent: 18, 63, and 32 of 64 codes used across seeds. This
script reads the recorded JSONs and lays out the spread.

Inputs (recorded, unchanged): ../runs/multi-speaker-seed*.json

Run:
    uv run python core/health_read.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    runs = Path(__file__).resolve().parents[2] / "runs"
    print("multi-speaker codebook health (recorded), read:")
    for seed in (0, 1, 2):
        with open(runs / f"multi-speaker-seed{seed}.json") as fh:
            d = json.load(fh)
        usage = d.get("codebook_usage", {})
        print(f"  seed {seed}: codes {usage.get('unique_codes_used')}/"
              f"{usage.get('codebook_size')}, entropy ratio "
              f"{usage.get('entropy_ratio', 0):.3f}, eval MSE "
              f"{d.get('codec_eval_mse', 0):.5f}")
    print("\nreading: no collapse in any seed, but the 18-vs-63 code spread is")
    print("seed-dependent — the same recipe that escaped reliably at 1-2")
    print("speakers no longer does at 10, which is the fix-generalization")
    print("gap stage 04 records.")


if __name__ == "__main__":
    main()
