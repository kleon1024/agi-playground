"""Detour 05-a -- the stall signature behind a timeout rate.

Stage 05 reports that on hard scenarios the cloned policy times out in 72%
of episodes with mean progress 12.2m. This script opens what a timeout is
made of: how far the car gets, how slowly it moves, whether it passes any
obstacles, and whether it is still making forward progress when the
episode ends. The expert is profiled on the same tracks for contrast --
its failures are collisions (a committed maneuver that was wrong), while
the clone's failures are stalls (no maneuver committed at all).

Usage:
    python stall_profile.py
"""

from __future__ import annotations

import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import torch

SIM_DIR = Path(__file__).resolve().parents[3] / "00-scenario-simulator" / "core"
EXP_DIR = Path(__file__).resolve().parents[3] / "02-expert-policy" / "core"
CLONE_DIR = Path(__file__).resolve().parents[3] / "03-behavior-cloning" / "core"
sys.path.insert(0, str(SIM_DIR))
sys.path.insert(0, str(EXP_DIR))
sys.path.insert(0, str(CLONE_DIR))
from clone import CloneNet
from driving_sim import (
    MAX_STEPS,
    ROAD_HALF_WIDTH,
    TARGET_X,
    Car,
    render,
    sample_scenario,
)
from expert import make_expert

RUNS = Path(__file__).resolve().parents[1] / "runs"
HARD_SEEDS = range(200, 250)
CREEP_SPEED = 0.5  # m/s below which we call the car creeping
STUCK_WINDOW = 50  # last N steps checked for forward progress
STUCK_PROGRESS_M = 1.0
X_BUCKETS = [(0, 15), (15, 30), (30, 45), (45, 60)]


def cloned_policy(model: CloneNet):
    def policy(obs, car):
        x = torch.from_numpy(np.asarray(obs, dtype=np.float32).reshape(-1) / 3.0)
        with torch.no_grad():
            ps, pt = model(x)
        return int(ps.argmax().item() - 1), int(pt.argmax().item())

    return policy


def _track_min_clearance(scenario, car):
    best = float("inf")
    for ox, oy, r, _ in scenario.obstacles:
        best = min(best, float(np.hypot(car.x - ox, car.y - oy)))
    return best


def profile_many(scenarios, policy_factory) -> dict:
    rows = []
    x_history = []
    for s in scenarios:
        car = Car()
        policy = policy_factory(s)
        creep = 0
        min_clear = float("inf")
        xs = []
        outcome = "timeout"
        for step in range(MAX_STEPS):
            obs = render(s, car)
            steer, throttle = policy(obs, car)
            car.step(steer, throttle)
            xs.append(car.x)
            if car.v < CREEP_SPEED:
                creep += 1
            min_clear = min(min_clear, _track_min_clearance(s, car))
            if car.x >= TARGET_X:
                outcome = "completed"
                break
            collided = False
            for ox, oy, r, _ in s.obstacles:
                if np.hypot(car.x - ox, car.y - oy) < r + 0.35:
                    collided = True
                    break
            if collided:
                outcome = "collision"
                break
            if abs(car.y - s.lane_center(car.x)) > ROAD_HALF_WIDTH:
                outcome = "offroad"
                break
        steps = len(xs)
        progress_end = car.x - (xs[-STUCK_WINDOW] if steps > STUCK_WINDOW else 0.0)
        obstacles_passed = sum(1 for ox, _oy, _r, _vx in s.obstacles if ox < car.x)
        rows.append(
            {
                "outcome": outcome,
                "x": round(car.x, 2),
                "steps": steps,
                "creep_fraction": round(creep / steps, 4),
                "progress_last_50": round(progress_end, 2),
                "stuck_at_end": bool(
                    outcome == "timeout" and progress_end < STUCK_PROGRESS_M
                ),
                "obstacles_passed": obstacles_passed,
                "final_speed": round(car.v, 3),
                "min_clearance": round(min_clear, 3),
            }
        )
        x_history.append(car.x)

    n = len(rows)
    outcomes = {}
    for name in ("completed", "collision", "offroad", "timeout"):
        outcomes[name] = round(sum(1 for r_ in rows if r_["outcome"] == name) / n, 3)
    timed_out = [r_ for r_ in rows if r_["outcome"] == "timeout"]
    completed = [r_ for r_ in rows if r_["outcome"] == "completed"]

    def mean(key, subset):
        return round(float(np.mean([r_[key] for r_ in subset])), 3) if subset else None

    buckets = {}
    for lo, hi in X_BUCKETS:
        buckets[f"{lo}-{hi}"] = round(
            sum(1 for x_ in x_history if lo <= x_ < hi) / n, 3
        )
    return {
        "scenarios": n,
        "outcome_rates": outcomes,
        "progress": {
            "mean_x": round(float(np.mean(x_history)), 2),
            "median_x": float(np.median(x_history)),
            "x_bucket_fractions": buckets,
        },
        "timed_out_episodes": {
            "count": len(timed_out),
            "mean_creep_fraction": mean("creep_fraction", timed_out),
            "stuck_at_end_fraction": round(
                sum(1 for r_ in timed_out if r_["stuck_at_end"]) / max(len(timed_out), 1), 3
            ),
            "mean_final_speed": mean("final_speed", timed_out),
            "mean_obstacles_passed": mean("obstacles_passed", timed_out),
            "mean_x": mean("x", timed_out),
        },
        "completed_episodes": {
            "count": len(completed),
            "mean_creep_fraction": mean("creep_fraction", completed),
        },
        "all_episodes_mean_creep_fraction": mean("creep_fraction", rows),
    }


def main() -> None:
    t0 = time.time()
    scenarios = [sample_scenario(seed, hard=True) for seed in HARD_SEEDS]
    model = CloneNet()
    model.load_state_dict(torch.load(CLONE_DIR / "cloned_policy.pt", weights_only=True))
    model.eval()

    expert = profile_many(scenarios, make_expert)
    t1 = time.time()
    cloned = profile_many(scenarios, lambda s: cloned_policy(model))
    t2 = time.time()

    RUNS.mkdir(parents=True, exist_ok=True)
    summary = {
        "command": "python stall_profile.py",
        "hardware": {
            "machine": platform.machine(),
            "system": platform.system(),
            "python": platform.python_version(),
        },
        "cost_usd": 0.0,
        "hard_expert": expert,
        "hard_cloned": cloned,
        "wall_clock_s": {
            "expert": round(t1 - t0, 2),
            "cloned": round(t2 - t1, 2),
            "total": round(t2 - t0, 2),
        },
    }
    with (RUNS / "2026-08-08-stall-profile.json").open("w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
