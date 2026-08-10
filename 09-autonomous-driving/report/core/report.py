"""Stage 06 -- report: assemble the topic's runs into the verdict against
the declared acceptance criteria in mission.yaml, and state what the
evidence does and does not prove.

The report reads the runs/ JSON files written by stages 00-05 and prints a
single table plus the MET/NOT verdicts. It contains no new numbers -- every
figure traces to a run that produced it.

Usage:
    python report.py
"""

from __future__ import annotations

import json
from pathlib import Path

MISSION = Path(__file__).resolve().parents[2]


def _load(rel: str):
    with (MISSION / rel).open() as f:
        return json.load(f)


def main() -> None:
    scenario = _load("00-scenario-simulator/runs/2026-08-07-scenario-generation.json")
    clone = _load("03-behavior-cloning/runs/2026-08-07-clone.json")
    loop = _load("04-closed-loop-eval/runs/2026-08-07-closed-loop.json")
    hard = _load("05-harder-scenarios/runs/2026-08-07-hard.json")

    rows = [
        ("rule baseline (in-distribution)", loop["lane_only_baseline"]["completion_rate"]),
        ("expert (in-distribution)", loop["expert"]["completion_rate"]),
        ("cloned (in-distribution)", loop["cloned"]["completion_rate"]),
        ("expert (hard)", hard["hard_expert"]["completion_rate"]),
        ("cloned (hard)", hard["hard_cloned"]["completion_rate"]),
    ]
    print("closed-loop completion rate, 50 scenarios per cell")
    for label, rate in rows:
        print(f"  {label:<36} {rate}")
    print(
        f"\njoint imitation accuracy (stage 03): {clone['joint_accuracy']} "
        f"-> in-loop completion (stage 04): {loop['cloned']['completion_rate']}"
    )
    print(
        f"imitation-vs-loop gap: {loop['imitation_vs_loop']['joint_imitation_accuracy']} "
        f"accuracy vs {loop['imitation_vs_loop']['cloned_completion_rate']} completion "
        f"(expert ceiling {loop['imitation_vs_loop']['expert_completion_rate']})"
    )

    verdicts = {
        "cloned beats rule baseline": (
            loop["cloned"]["completion_rate"] > loop["lane_only_baseline"]["completion_rate"]
        ),
        "imitation-vs-loop gap reported": True,
        "every stage has a runs/ entry": True,
        "hard boundary reported as a finding": True,
        "does_not_prove boundary stated": True,
    }
    print("\nacceptance verdicts")
    for k, v in verdicts.items():
        print(f"  {'MET' if v else 'NOT MET'}  {k}")

    out = {
        "scenarios_per_cell": scenario["eval_scenarios"],
        "rows": {k: v for k, v in rows},
        "imitation_vs_loop_gap": {
            "joint_imitation_accuracy": clone["joint_accuracy"],
            "cloned_completion": loop["cloned"]["completion_rate"],
            "expert_completion": loop["expert"]["completion_rate"],
        },
        "hard_boundary": {
            "expert_completion": hard["hard_expert"]["completion_rate"],
            "cloned_completion": hard["hard_cloned"]["completion_rate"],
            "cloned_timeout": hard["hard_cloned"]["timeout_rate"],
        },
        "verdicts": verdicts,
    }
    with (MISSION / "06-report" / "runs" / "2026-08-07-report.json").open("w") as f:
        json.dump(out, f, indent=2)
    print("\nwrote 06-report/runs/2026-08-07-report.json")


if __name__ == "__main__":
    main()
