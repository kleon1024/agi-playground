"""The format-credit trap, read from the recorded tool-use RL run.

Stage 06's reward gives format credit for emitting legal A/T characters
and outcome credit for correct digit counts. This script reads the
recorded seed JSONs and lays out what the policy actually learned — the
format credit it can earn without solving the task.

Inputs (recorded, unchanged): ../runs/grpo-seed*.json

Run:
    uv run python core/format_trap_read.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    runs = Path(__file__).resolve().parents[2] / "runs"
    print("tool-use RL, read from the recorded seeds:")
    for seed in (0, 1, 2):
        with open(runs / f"grpo-seed{seed}.json") as fh:
            d = json.load(fh)
        g = d["eval_greedy"]
        # per-level: answer_rate (direct answer, no tool) vs tool_rate
        ans = g["per_level"]["1"]["answer_rate"]
        tool = g["per_level"]["5"]["tool_rate"]
        print(f"  seed {seed}: mean reward {g['mean_reward']:.3f} | "
              f"level-1 answer_rate {ans:.2f} | level-5 tool_rate {tool:.2f}")
    print("\nreading: the policy answers easy levels directly (answer_rate 1.00")
    print("at level 1 in every seed) — but only seed 0 pays for the tool at the")
    print("hard level (tool_rate 1.00 at level 5); seeds 1-2 stop paying, which")
    print("is the tool-rate collapse the mission records.")


if __name__ == "__main__":
    main()
