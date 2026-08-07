"""The honest NOT MET: the verdict's evidence structure, recomputed.

Mission 06's outcome report judged GRPO against both baselines and
catalogued the failures. This script reads the committed baselines and GRPO
seed JSONs and recomputes the margins against the policy's own seed spread
— the move that makes the verdict honest. The failure catalogue is the
recorded report's, cited.

Run:
    uv run python core/not_met_report.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def main() -> None:
    with open(ROOT / "00-gridworld-baselines" / "runs" / "baselines.json") as fh:
        baselines = json.load(fh)["results"]
    random_b = baselines["random"]["success_rate"]
    greedy_b = baselines["greedy"]["success_rate"]

    greedy_scores, sampled_scores = [], []
    for seed in (0, 1, 2):
        with open(ROOT / "01-grpo" / "runs" / f"grpo-seed{seed}.json") as fh:
            d = json.load(fh)
        greedy_scores.append(d["eval_greedy"]["success_rate"])
        sampled_scores.append(d["eval_sampled"]["success_rate"])

    g_mean = statistics.fmean(greedy_scores)
    g_spread = max(greedy_scores) - min(greedy_scores)
    s_mean = statistics.fmean(sampled_scores)
    s_spread = max(sampled_scores) - min(sampled_scores)

    print("mission 06 outcome report, margins recomputed from the recorded JSONs")
    print(f"  baselines: random {random_b:.4f}, greedy {greedy_b:.4f}")
    print(f"  GRPO greedy decode {g_mean:.4f}+-{g_spread:.4f} | sampled {s_mean:.4f}+-{s_spread:.4f}")
    print("\n  margins vs the policy's own seed spread:")
    for label, mean, spread, baseline in (
        ("greedy decode", g_mean, g_spread, random_b),
        ("sampled decode", s_mean, s_spread, random_b),
        ("greedy decode", g_mean, g_spread, greedy_b),
        ("sampled decode", s_mean, s_spread, greedy_b),
    ):
        margin = mean - baseline
        verdict = "decisively loses" if abs(margin) > spread else "within noise"
        bl = "random" if baseline == random_b else "greedy"
        print(f"  {label} vs {bl}: {margin:+.4f} vs spread {spread:.4f} -> {verdict}")

    print("\n  failure catalogue (recorded): degenerate groups 0/0/1 of 200,")
    print("  board-independent collapse 3/3, non-stabilizing success 3/3 —")
    print("  the verdict is NOT MET because the margins lose and the")
    print("  catalogue explains why, not just that.")


if __name__ == "__main__":
    main()
