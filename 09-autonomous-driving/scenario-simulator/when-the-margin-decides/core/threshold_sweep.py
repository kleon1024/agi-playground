"""Detour 00-a -- which knob in the episode contract decides the outcome.

Stage 00 declares the episode contract: an episode ends in collision when an
obstacle is closer than r + 0.35m, and in completion when the car passes
TARGET_X = 60m. Two knobs in that contract are free parameters: the collision
margin and the target distance. This script sweeps both and measures how far
each moves the reported completion rate for the expert and the lane-only
floor on the same 50 eval scenarios.

The finding is a sensitivity asymmetry. The expert's failures sit on the
collision margin -- 0.96 completion at a 0.20m margin, 0.86 at 0.50m -- while
the floor's collisions are deep and barely move, and the target distance is
inert. A completion rate is only comparable when the collision threshold is
fixed; the contract's meaningful knob is the margin, not the goal.

Usage:
    python threshold_sweep.py
"""

from __future__ import annotations

import json
import math
import platform
import sys
import time
from pathlib import Path

SIM_DIR = Path(__file__).resolve().parents[2] / "core"
EXP_DIR = Path(__file__).resolve().parents[2] / ".." / "02-expert-policy" / "core"
sys.path.insert(0, str(SIM_DIR))
sys.path.insert(0, str(EXP_DIR))
from driving_sim import (
    MAX_STEPS,
    ROAD_HALF_WIDTH,
    TARGET_X,
    Car,
    render,
    sample_scenario,
)
from expert import lane_only_policy, make_expert

RUNS = Path(__file__).resolve().parents[1] / "runs"
EVAL_SEEDS = range(100, 150)
MARGINS = [0.20, 0.30, 0.40, 0.50]
TARGETS = [55.0, 60.0, 65.0]
STANDARD_MARGIN = 0.35


def simulate_with(
    scenario,
    policy,
    margin: float,
    target_x: float,
    max_steps: int = MAX_STEPS,
):
    """driving_sim.simulate with the contract knobs as parameters.

    Collision uses `r + margin` instead of the hardcoded `r + 0.35`, and the
    episode ends at `target_x` instead of the module TARGET_X. Returns the
    outcome plus, for the margin analysis, the per-obstacle clearance slack
    at the closest approach: d - (r + margin), in metres.
    """
    car = Car()
    min_slack = float("inf")
    min_slack_obs = None
    for step in range(max_steps):
        obs = render(scenario, car)
        steer, throttle = policy(obs, car)
        car.step(steer, throttle)
        off = abs(car.y - scenario.lane_center(car.x))
        for ox, oy, r, _ in scenario.obstacles:
            d = math.hypot(car.x - ox, car.y - oy)
            slack = d - (r + margin)
            if slack < min_slack:
                min_slack = slack
                min_slack_obs = (ox, oy, r)
            if d < r + margin:
                return {
                    "outcome": "collision",
                    "steps": step + 1,
                    "x": car.x,
                    "min_slack": min_slack,
                    "min_slack_obs": min_slack_obs,
                }
        if off > ROAD_HALF_WIDTH:
            return {
                "outcome": "offroad",
                "steps": step + 1,
                "x": car.x,
                "min_slack": min_slack,
                "min_slack_obs": min_slack_obs,
            }
        if car.x >= target_x:
            return {
                "outcome": "completed",
                "steps": step + 1,
                "x": car.x,
                "min_slack": min_slack,
                "min_slack_obs": min_slack_obs,
            }
    return {
        "outcome": "timeout",
        "steps": max_steps,
        "x": car.x,
        "min_slack": min_slack,
        "min_slack_obs": min_slack_obs,
    }


def sweep(policy_factory, margin: float, target_x: float) -> dict:
    outcomes = []
    fail_seeds = []
    for seed in EVAL_SEEDS:
        s = sample_scenario(seed)
        res = simulate_with(s, policy_factory(s), margin, target_x)
        outcomes.append(res["outcome"])
        if res["outcome"] != "completed":
            fail_seeds.append(seed)
    n = len(outcomes)
    return {
        "margin": margin,
        "target_x": target_x,
        "completion_rate": round(outcomes.count("completed") / n, 3),
        "collision_rate": round(outcomes.count("collision") / n, 3),
        "offroad_rate": round(outcomes.count("offroad") / n, 3),
        "timeout_rate": round(outcomes.count("timeout") / n, 3),
        "fail_seeds": fail_seeds,
    }


def slack_distribution(policy_factory, margin: float, target_x: float) -> dict:
    """How close completed episodes came to the collision line."""
    completed_slacks = []
    for seed in EVAL_SEEDS:
        s = sample_scenario(seed)
        res = simulate_with(s, policy_factory(s), margin, target_x)
        if res["outcome"] == "completed":
            completed_slacks.append(res["min_slack"])
    if not completed_slacks:
        return {"completed": 0}
    completed_slacks.sort()
    within = {
        "0.10": sum(1 for x in completed_slacks if x < 0.10),
        "0.15": sum(1 for x in completed_slacks if x < 0.15),
        "0.25": sum(1 for x in completed_slacks if x < 0.25),
    }
    return {
        "completed": len(completed_slacks),
        "completed_with_slack_lt_m": within,
        "min_slack_m": round(completed_slacks[0], 3),
        "median_slack_m": round(completed_slacks[len(completed_slacks) // 2], 3),
    }


def main() -> None:
    t0 = time.time()
    experts, floors = [], []
    for margin in MARGINS:
        experts.append(sweep(lambda s, m=margin: make_expert(s), margin, TARGET_X))
        floors.append(
            sweep(lambda s, m=margin: (lambda obs, car: lane_only_policy(s, obs, car)), margin, TARGET_X)
        )

    target_rows = []
    for target in TARGETS:
        target_rows.append(sweep(make_expert, STANDARD_MARGIN, target))

    # The 50 eval scenarios replayed at the standard margin, with the
    # per-scenario clearance slack of completed episodes.
    slack_expert = slack_distribution(make_expert, STANDARD_MARGIN, TARGET_X)

    # The scenarios that flip between the loosest and tightest margins are
    # the marginal ones -- the same seeds sit on the collision line.
    flip_expert = sorted(
        set(experts[0]["fail_seeds"]) ^ set(experts[-1]["fail_seeds"])
    )

    result = {
        "command": "python threshold_sweep.py",
        "hardware": {
            "machine": platform.machine(),
            "system": platform.system(),
            "python": platform.python_version(),
        },
        "cost_usd": 0.0,
        "scenarios": 50,
        "standard_margin_m": STANDARD_MARGIN,
        "expert_margin_sweep": experts,
        "floor_margin_sweep": floors,
        "expert_target_sweep": target_rows,
        "expert_slack_at_standard_margin": slack_expert,
        "expert_flip_seeds_between_0_20_and_0_50": flip_expert,
        "wall_clock_s": round(time.time() - t0, 2),
    }
    RUNS.mkdir(parents=True, exist_ok=True)
    with (RUNS / "2026-08-08-margin-sweep.json").open("w") as f:
        json.dump(result, f, indent=2)

    print("expert margin sweep:")
    for row in experts:
        print(f"  margin {row['margin']}: comp {row['completion_rate']} "
              f"coll {row['collision_rate']} fails {row['fail_seeds']}")
    print("floor margin sweep:")
    for row in floors:
        print(f"  margin {row['margin']}: comp {row['completion_rate']} "
              f"coll {row['collision_rate']} fails {row['fail_seeds']}")
    print("expert target sweep:")
    for row in target_rows:
        print(f"  target {row['target_x']}: comp {row['completion_rate']} "
              f"coll {row['collision_rate']}")
    print("expert slack at standard margin:", json.dumps(slack_expert, indent=2))
    print("flip seeds between margins 0.20 and 0.50:", flip_expert)
    print("wall_clock_s:", result["wall_clock_s"])


if __name__ == "__main__":
    main()
