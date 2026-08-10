"""The flipped variance, read from the recorded real-photo fusion run.

Stage 04's result on real photographs flipped the variance structure: the
text-only arm is now the noisy one (spread 0.0707) while vision is stable
(0.0051), the opposite of stage 01's synthetic case. This script reads the
recorded JSON and lays out the per-seed numbers.

Input (recorded, unchanged): ../runs/real-photo-results.json

Run:
    uv run python core/flip_variance_read.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    with open(
        Path(__file__).resolve().parents[2] / "runs" / "real-photo-results.json"
    ) as fh:
        d = json.load(fh)
    vis, txt = d["vision_per_seed"], d["text_only_per_seed"]
    print("real-photo vision vs text-only (recorded), read:")
    print(f"  vision:    {[round(x,4) for x in vis]}  "
          f"spread {max(vis)-min(vis):.4f}")
    print(f"  text-only: {[round(x,4) for x in txt]}  "
          f"spread {max(txt)-min(txt):.4f}")
    print(f"  margin: +{sum(vis)/3 - sum(txt)/3:.4f}")
    print("\nreading: the noise flipped arms — text-only is now 7x noisier,")
    print("the opposite of stage 01's synthetic case, and the narrow margin")
    print("belongs to a stable vision pathway, not two equally noisy ones.")


if __name__ == "__main__":
    main()
