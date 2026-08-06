"""The compounding axes, read from the recorded fourth-corner run.

Stage 06 ran both axes together: 16 frames and 2 objects. This script
reads the recorded JSONs and lays out where the difficulties compound.

Inputs (recorded, unchanged): ../runs/longer-and-multi-object-seed*.json

Run:
    uv run python core/axes_compound.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    runs = Path(__file__).resolve().parents[2] / "runs"
    print("the fourth corner (16 frames + 2 objects), read:")
    for seed in (0, 1, 2):
        with open(runs / f"longer-and-multi-object-seed{seed}.json") as fh:
            d = json.load(fh)
        g = d["generation"]
        m = g["reconstruction_mse"]
        print(f"  seed {seed}: lm {m['lm_completion']:.4f} vs baseline "
              f"{m['frame_repeat_baseline']:.4f}, exact "
              f"{g['predicted_token_sequence_exact_match_rate']:.4f}, "
              f"verdict {g['verdict']}")
    print("\nreading: in pixel space the axes do not add (MSE inside the range")
    print("the second object alone cost), but in token space exact-match")
    print("collapses to near zero — the one-token-per-frame capacity is the")
    print("binding constraint, and the verdict still closes MET.")


if __name__ == "__main__":
    main()
