"""The object-count axis, read: one object vs two per-frame tokens.

Stage 05 composited two independently-moving shapes into one scene while
the codec still emits one 64-entry token per frame. This script reads the
recorded single-object (stage 02) and two-object (stage 05) generation
JSONs and lays out the capacity question: what does the second object cost
when one token must represent both positions.

Inputs (recorded, unchanged): stage 02 and stage 05 committed seed JSONs.

Run:
    uv run python core/object_axis.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path


def main() -> None:
    mission = Path(__file__).resolve().parents[3]
    ones, twos = [], []
    for seed in (0, 1, 2):
        d1 = json.loads(
            (mission / "02-generation-model" / "runs" / f"generation-seed{seed}.json").read_text()
        )
        d2 = json.loads(
            (Path(__file__).resolve().parents[2] / "runs" / f"multi-object-seed{seed}.json").read_text()
        )["generation"]
        ones.append(d1["reconstruction_mse"]["lm_completion"])
        twos.append(d2["reconstruction_mse"]["lm_completion"])
        print(
            f"seed {seed}: 1-obj mse {d1['reconstruction_mse']['lm_completion']:.4f} "
            f"| 2-obj mse {d2['reconstruction_mse']['lm_completion']:.4f} "
            f"exact {d2['predicted_token_sequence_exact_match_rate']:.3f}"
        )
    print(f"\n1-obj mean {statistics.fmean(ones):.4f}, 2-obj mean {statistics.fmean(twos):.4f}")
    print("reading: one token per frame has to carry both objects' positions,")
    print("and the reconstruction cost is where the capacity limit shows.")


if __name__ == "__main__":
    main()
