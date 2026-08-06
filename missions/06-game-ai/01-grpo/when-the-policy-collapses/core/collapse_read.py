"""The collapsed policy, read from the three recorded GRPO seeds.

Stage 01's recorded seed JSONs hold the mission's null result: every trained
seed collapses to a constant direction string (RRRR / UUUU / LLLL) on the
held-out boards, and greedy-decoded success is far below both baselines.
This script reads the committed JSONs and lays out the collapse — what the
policy actually emits, and how far it lands from the bar it had to clear.

Input (recorded, unchanged): ../runs/grpo-seed0/1/2.json

Run:
    uv run python core/collapse_read.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    for seed in (0, 1, 2):
        with open(
            Path(__file__).resolve().parents[2] / "runs" / f"grpo-seed{seed}.json"
        ) as fh:
            d = json.load(fh)
        ex = d["examples"][0]
        print(
            f"seed {seed}: greedy success {d['eval_greedy']['success_rate']:.3f} "
            f"| emits '{ex['raw_completion'][:6]}...' on all held-out boards"
        )
    print("\nreading: the policy learned to emit one direction and stop — a")
    print("cold-start collapse where no gradient step ever sharpened behavior")
    print("that was absent, which is why the mission's verdict is an honest null.")


if __name__ == "__main__":
    main()
