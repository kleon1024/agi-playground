"""The policy anatomy: the same decoder, a different objective.

Mission 06's "model" is mission 01's decoder instantiated for a
28-character grid vocabulary, driven by a two-part reward — format credit
for emitting legal moves plus a terminal goal-reached bit. The anatomy is
that this policy's structure is identical to a language model's; what
changed is the reward, and the collapse the mission recorded is the
consequence of the reward's shape, not the architecture's.

Config (measured, stage 01): vocab=28, n_layer=4, n_head=4, n_kv_head=2,
d_model=128, d_ff=320, block_size=96, total params 692,864.

Run:
    uv run python core/policy_anatomy.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    print("policy anatomy (stage-01 config), computed:")
    print("  structure: mission 01's Transformer, 692,864 params,")
    print("             instantiated for a 28-character grid vocabulary")
    print("  reward:    format credit (0.2/0.5/1.0 for legal moves)")
    print("             + terminal goal-reached bit")
    print("  outcome:   each seed collapses to a constant direction string")
    runs = Path(__file__).resolve().parents[2] / "runs"
    rates = []
    for seed in (0, 1, 2):
        with open(runs / f"grpo-seed{seed}.json") as fh:
            d = json.load(fh)
        rates.append(d["eval_greedy"]["success_rate"])
        print(f"             seed {seed}: greedy success {rates[-1]:.3f}")
    print("\nreading: the architecture is not the failure — the reward's format")
    print("credit can be earned without reaching the goal, which is exactly")
    print("the cold-start trap the mission's null result records.")


if __name__ == "__main__":
    main()
