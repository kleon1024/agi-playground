"""The revived codebook, read from the recorded video-codec run.

Stage 01's first three training attempts collapsed to a single failure
mode each, and the final run revived 158 dead codes. This script reads the
recorded JSON and lays out the final codebook health and the collapse
history.

Input (recorded, unchanged): ../runs/video-codec-seed0.json

Run:
    uv run python core/revive_read.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    with open(
        Path(__file__).resolve().parents[2] / "runs" / "video-codec-seed0.json"
    ) as fh:
        d = json.load(fh)
    usage = d["codebook_usage"]
    print("video codec (recorded), read:")
    print(f"  eval MSE {d['eval_mse_codec']:.5f} vs background "
          f"{d['baseline_mse']['background']:.5f} / mean-frame "
          f"{d['baseline_mse']['mean_frame']:.5f}")
    print(f"  codes used {usage['unique_codes_used']}/{usage['codebook_size']}, "
          f"entropy ratio {usage['entropy_ratio']:.3f}")
    print(f"  dead codes revived: {d['dead_codes_revived_total']} "
          f"(revive every {d['revive_every']} steps)")
    print("\nreading: three collapse attempts preceded this — codebook collapse,")
    print("then the decoder saturation bug — and the revive mechanism is what")
    print("kept the codebook at 63/64 while training stabilized.")


if __name__ == "__main__":
    main()
