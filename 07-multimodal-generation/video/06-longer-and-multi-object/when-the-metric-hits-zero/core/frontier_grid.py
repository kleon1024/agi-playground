"""The feasibility frontier, read from the recorded grid corners.

The mission's generation stages sample a grid: frames (8, 16) x objects
(1, 2), and each corner's recorded run reports reconstruction MSE and the
token exact-match rate. This script assembles the four corners from the
recorded JSONs so the frontier — which axis costs more, and when the token
metric hits zero while the pixel metric still holds — is one table.

Inputs (recorded): stage 02, 04, 05, 06 generation-seed*.json.

Run:
    uv run python core/frontier_grid.py
"""

from __future__ import annotations

import json
from pathlib import Path


def mse_of(root: Path, stage: str) -> tuple[float, float]:
    with open(root / stage / "runs" / "generation-seed0.json") as fh:
        d = json.load(fh)
    m = d["reconstruction_mse"]
    return m["lm_completion"], m["frame_repeat_baseline"]


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    corners = (
        ("8 frames x 1 object", "02-generation-model"),
        ("16 frames x 1 object", "04-longer-sequences"),
        ("8 frames x 2 objects", "05-multi-object"),
        ("16 frames x 2 objects", "06-longer-and-multi-object"),
    )
    print(f"{'corner':<24} {'lm MSE':>8} {'frame-repeat':>13}")
    for label, stage in corners:
        lm, fr = mse_of(root, stage)
        print(f"{label:<24} {lm:>8.4f} {fr:>13.4f}")


if __name__ == "__main__":
    main()
