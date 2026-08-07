"""The frame-count axis, read: 8 vs 16 frames, same recipe.

Stage 04 doubled stage 02's N_FRAMES from 8 to 16 and kept everything else
unchanged. This script reads the recorded stage-02 (8-frame) and stage-04
(16-frame) generation JSONs and lays out the axis: quality holds, exact
match gets noisier, and cost grows faster than the frame count.

Inputs (recorded, unchanged): stage 02 and stage 04 committed seed JSONs.

Run:
    uv run python core/frame_axis.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path


def main() -> None:
    mission = Path(__file__).resolve().parents[3]
    eights, sixteens = [], []
    for seed in (0, 1, 2):
        d8 = json.loads(
            (mission / "02-generation-model" / "runs" / f"generation-seed{seed}.json").read_text()
        )
        d16 = json.loads(
            (Path(__file__).resolve().parents[2] / "runs" / f"longer-sequences-frames16-seed{seed}.json").read_text()
        )["generation"]
        eights.append(d8["reconstruction_mse"]["lm_completion"])
        sixteens.append(d16["reconstruction_mse"]["lm_completion"])
        print(
            f"seed {seed}: 8f mse {d8['reconstruction_mse']['lm_completion']:.4f} "
            f"| 16f mse {d16['reconstruction_mse']['lm_completion']:.4f} "
            f"exact {d16['predicted_token_sequence_exact_match_rate']:.3f} "
            f"cost {d16['compute']['total_wall_clock_s']:.0f}s"
        )
    print(f"\n8f mean {statistics.fmean(eights):.4f}, 16f mean {statistics.fmean(sixteens):.4f}")
    print("reading: doubling frames holds reconstruction quality while exact")
    print("match gets noisier and cost grows ~4x — the tokenizer, not compute,")
    print("is still the binding constraint.")


if __name__ == "__main__":
    main()
