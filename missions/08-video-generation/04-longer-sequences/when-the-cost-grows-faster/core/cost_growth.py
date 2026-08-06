"""The cost growth that outruns the frames, read from the recorded runs.

Stage 04 doubled N_FRAMES from 8 to 16 and wall-clock grew ~4x. This
script reads the recorded JSONs and lays out the growth on both axes.

Inputs (recorded, unchanged): stage-02 generation JSONs and stage-04
longer-sequences JSONs.

Run:
    uv run python core/cost_growth.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    mission = Path(__file__).resolve().parents[3]
    eight_costs, sixteen_costs = [], []
    for seed in (0, 1, 2):
        d8 = json.loads(
            (mission / "02-generation-model" / "runs" / f"generation-seed{seed}.json").read_text()
        )
        d16 = json.loads(
            (Path(__file__).resolve().parents[2] / "runs" / f"longer-sequences-frames16-seed{seed}.json").read_text()
        )["generation"]
        eight_costs.append(d8["compute"]["total_wall_clock_s"])
        sixteen_costs.append(d16["compute"]["total_wall_clock_s"])
        print(f"  seed {seed}: 8f {eight_costs[-1]:.0f}s, 16f {sixteen_costs[-1]:.0f}s")
    mean8 = sum(eight_costs) / 3
    mean16 = sum(sixteen_costs) / 3
    print(f"\n  mean {mean8:.0f}s -> {mean16:.0f}s = {mean16/mean8:.1f}x for a 2x frame count")
    print("\nreading: cost grows ~4x for 2x frames — more than the codec's")
    print("roughly-linear prediction, because the LM's attention cost grows")
    print("faster than linear too.")


if __name__ == "__main__":
    main()
