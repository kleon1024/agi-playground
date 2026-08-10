"""Stage 04 -- closed-loop evaluation: run the cloned policy in the loop
on the eval scenarios and compare it against the no-learning rule baseline
and the expert on the same scenarios.

This is where imitation learning's known failure shows. Stage 03 measured
imitation accuracy on expert states; here the policy's own actions put the
car in states the expert never visited, and small errors compound. The
report pairs held-out imitation accuracy beside in-loop completion rate on
purpose -- a high imitation accuracy with a low completion rate is exactly
the compounding-error gap this topic exists to measure.

Usage:
    python eval_loop.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

SIM_DIR = Path(__file__).resolve().parents[2] / "00-scenario-simulator" / "core"
EXP_DIR = Path(__file__).resolve().parents[2] / "02-expert-policy" / "core"
CLONE_DIR = Path(__file__).resolve().parents[2] / "03-behavior-cloning" / "core"
sys.path.insert(0, str(SIM_DIR))
sys.path.insert(0, str(EXP_DIR))
sys.path.insert(0, str(CLONE_DIR))
from clone import CloneNet
from driving_sim import (
    sample_scenario,
    simulate,
)
from expert import lane_only_policy, make_expert

RUNS = Path(__file__).resolve().parents[1] / "runs"
EVAL_SEEDS = range(100, 150)


def cloned_policy(model: CloneNet):
    def policy(obs, car):
        x = torch.from_numpy(np.asarray(obs, dtype=np.float32).reshape(-1) / 3.0)
        with torch.no_grad():
            ps, pt = model(x)
        return int(ps.argmax().item() - 1), int(pt.argmax().item())

    return policy


def _eval(scenarios, policy_factory):
    results = {"completed": 0, "collided": 0, "offroad": 0, "timeout": 0,
               "x": []}
    for s in scenarios:
        out = simulate(s, policy_factory(s))
        if out.completed:
            results["completed"] += 1
        elif out.collided:
            results["collided"] += 1
        elif out.offroad:
            results["offroad"] += 1
        else:
            results["timeout"] += 1
        results["x"].append(out.x_reached)
    n = len(scenarios)
    return {
        "scenarios": n,
        "completion_rate": round(results["completed"] / n, 3),
        "collision_rate": round(results["collided"] / n, 3),
        "offroad_rate": round(results["offroad"] / n, 3),
        "timeout_rate": round(results["timeout"] / n, 3),
        "mean_x_reached": round(float(np.mean(results["x"])), 2),
    }


def main() -> None:
    scenarios = [sample_scenario(seed) for seed in EVAL_SEEDS]
    model = CloneNet()
    model.load_state_dict(torch.load(CLONE_DIR / "cloned_policy.pt", weights_only=True))
    model.eval()

    t0 = time.time()
    lane_only = _eval(scenarios, lambda s: lambda obs, car: lane_only_policy(s, obs, car))
    lane_only["wall_clock_s"] = round(time.time() - t0, 2)
    t0 = time.time()
    expert = _eval(scenarios, make_expert)
    expert["wall_clock_s"] = round(time.time() - t0, 2)
    t0 = time.time()
    cloned = _eval(scenarios, lambda s: cloned_policy(model))
    cloned["wall_clock_s"] = round(time.time() - t0, 2)

    RUNS.mkdir(parents=True, exist_ok=True)
    clone_run = json.loads(
        (Path(__file__).resolve().parents[2] / "03-behavior-cloning" / "runs" / "2026-08-07-clone.json").read_text()
    )
    summary = {
        "lane_only_baseline": lane_only,
        "expert": expert,
        "cloned": cloned,
        "imitation_vs_loop": {
            "joint_imitation_accuracy": clone_run["joint_accuracy"],
            "cloned_completion_rate": cloned["completion_rate"],
            "expert_completion_rate": expert["completion_rate"],
        },
    }
    with (RUNS / "2026-08-07-closed-loop.json").open("w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
