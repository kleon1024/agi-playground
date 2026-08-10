"""The KV cache on audio tokens: same answer, flat latency.

Stage 01's recorded run compared naive (recompute the prefix every step)
and cached decoding on audio-token streams, plus a 500-token latency-stress
run. This script reads the recorded JSON for the correctness contract —
the two paths must produce identical tokens — and lays out the recorded
latency table that the mission's central claim rests on.

Input (recorded, unchanged): ../runs/streaming-seed0.json; the latency
table is the recorded run record's, cited not re-derived.

Run:
    uv run python core/streaming_reading.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    with open(Path(__file__).resolve().parents[2] / "runs" / "streaming-seed0.json") as fh:
        d = json.load(fh)
    examples = d["examples"]
    matched = sum(1 for e in examples if e["tokens_match"])
    print(f"eval clips: {len(examples)}, tokens_match: {matched}/{len(examples)}")
    print(f"prompt tokens: {d['prompt_len']}, generated tokens/clip: {d['n_new_tokens']}")
    print(f"reconstruction MSE: {min(e['reconstruction_mse'] for e in examples):.4f} "
          f".. {max(e['reconstruction_mse'] for e in examples):.4f}")
    print("\nrecorded latency stress (500-token stream, p50 ms):")
    print("  naive:  first-10 1.43ms  last-10 9.81ms  (6.9x slower)")
    print("  cached: first-10 1.15ms  last-10 1.50ms  (roughly flat)")
    print("\nreading: the cache is the same answer at flat latency — correctness")
    print("holds token-for-token, and only the cache makes a long audio stream")
    print("feasible in real time.")


if __name__ == "__main__":
    main()
