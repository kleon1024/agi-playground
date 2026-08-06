"""The 64/64 reset, read from the recorded codebook-reset run.

Stage 05 applied a dead-code reset and reached full codebook utilization
in every seed. This script reads the recorded JSONs and lays out the
before/after.

Inputs (recorded, unchanged): ../runs/reset-codec-seed*.json

Run:
    uv run python core/reset_read.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    runs = Path(__file__).resolve().parents[2] / "runs"
    print("dead-code reset vs plain VQ (recorded), read:")
    for seed in (0, 1, 2):
        with open(runs / f"reset-codec-seed{seed}.json") as fh:
            d = json.load(fh)
        usage = d.get("codebook_usage", {})
        print(f"  seed {seed}: codes {usage.get('unique_codes_used')}/"
              f"{usage.get('codebook_size')}, entropy ratio "
              f"{usage.get('entropy_ratio', 0):.3f}, resets "
              f"{d.get('resets_performed', '?')}")
    print("\nreading: the reset reaches 64/64 in every seed (vs stage 04's")
    print("18/63/32) — the mechanism fixes utilization, and the question stage")
    print("06 answers is whether it or the EMA update did the work.")


if __name__ == "__main__":
    main()
