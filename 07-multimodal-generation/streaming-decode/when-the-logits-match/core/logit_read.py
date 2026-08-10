"""The logit-level equality, read from the recorded streaming run.

Stage 01's claim is that cached decode produces identical output to full
recompute — checked at logit level, not token-id level. This script reads
the recorded JSON and lays out the gap numbers.

Input (recorded, unchanged): ../runs/streaming-seed0.json

Run:
    uv run python core/logit_read.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    with open(
        Path(__file__).resolve().parents[2] / "runs" / "streaming-seed0.json"
    ) as fh:
        d = json.load(fh)
    c = d["correctness"]
    print("streaming decode correctness (recorded), read:")
    print(f"  clips matched: {c['n_clips_tokens_matched']}/{c['n_clips_total']}")
    print(f"  max logit gap: {c['max_logit_gap_over_all_clips']:.2e}")
    print(f"  mean logit gap: {c['mean_logit_gap']:.2e}")
    print("\nreading: identical tokens could hide a confidence shift, so the")
    print("check is at logit level — a max gap of 1e-5 is machine noise, not")
    print("similarity. The zero quality gap is what makes the latency win a")
    print("pure win rather than a different model.")


if __name__ == "__main__":
    main()
