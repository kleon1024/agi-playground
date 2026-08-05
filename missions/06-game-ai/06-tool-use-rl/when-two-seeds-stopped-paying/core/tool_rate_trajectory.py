"""The tool-use policy's rate trajectory: why 1 of 3 seeds calibrated.

Stage 06's recorded run reports 1/3 seeds calibrated and 2/3 collapsed to
always-answer. This script reads the three recorded histories and lays out
the per-step `tool_rate` — the fraction of completions that paid for the
tool — so the collapse is a trajectory, not a verdict. The calibrated seed
should keep a difficulty-conditioned rate; the collapsed seeds should fall
to zero and stay there.

Inputs (recorded, unchanged): ../runs/grpo-seed{0,1,2}.json

Run:
    uv run python core/tool_rate_trajectory.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[2] / "runs"
    print(f"{'seed':>4} {'tool_rate early':>15} {'mid':>7} {'late':>7} {'final greedy':>13}")
    for seed in (0, 1, 2):
        with open(root / f"grpo-seed{seed}.json") as fh:
            d = json.load(fh)
        h = d["history"]
        rates = [step["tool_rate"] for step in h if "tool_rate" in step]
        if not rates:
            continue
        n = len(rates)
        early, mid, late = rates[0], rates[n // 2], rates[-1]
        greedy = d.get("eval_greedy", {}).get("success_rate", float("nan"))
        print(f"{seed:>4} {early:>15.3f} {mid:>7.3f} {late:>7.3f} {greedy:>13.3f}")


if __name__ == "__main__":
    main()
