"""Detour 04-a -- where the open-loop errors live, and why they compound.

Stage 04 reports that 0.7718 joint imitation accuracy becomes 0.28 in-loop
completion. This script opens that gap in two parts.

Part 1 (per-class error): on the expert's eval-scenario states, imitation
error is not spread evenly over actions -- it concentrates on the rare
dodge frames (steer nonzero), which are exactly the frames that decide an
episode.

Part 2 (closed-loop divergence): run the expert and the clone in the loop
on the same scenarios and measure when the clone's trajectory leaves the
expert's. Then label the clone's own visited states with the expert's
action -- the DAgger question: on the states the learner actually drives,
how often would the expert act differently?

Usage:
    python error_origin.py
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
    collect_demos,
    render,
    sample_scenario,
)
from expert import make_expert

RUNS = Path(__file__).resolve().parents[1] / "runs"
EVAL_SEEDS = range(100, 150)
STEER_LABELS = {-1: "left", 0: "center", 1: "right"}
DIVERGE_LAT_M = 0.5


def cloned_policy(model: CloneNet):
    def policy(obs, car):
        x = torch.from_numpy(np.asarray(obs, dtype=np.float32).reshape(-1) / 3.0)
        with torch.no_grad():
            ps, pt = model(x)
        return int(ps.argmax().item() - 1), int(pt.argmax().item())

    return policy


def _episode_end(s, car) -> str:
    """Same termination rules as driving_sim.simulate()."""
    for ox, oy, r, _ in s.obstacles:
        if np.hypot(car.x - ox, car.y - oy) < r + 0.35:
            return "collision"
    if abs(car.y - s.lane_center(car.x)) > ROAD_HALF_WIDTH:
        return "offroad"
    if car.x >= TARGET_X:
        return "completed"
    return ""


def per_class_errors(model: CloneNet, scenarios) -> dict:
    """Part 1 -- imitation accuracy split by the expert's true action."""
    frames, steer, throttle = [], [], []
    for s in scenarios:
        demos, _ = collect_demos([s], make_expert(s))
        for grid, st, th in demos:
            frames.append(np.asarray(grid, dtype=np.float32).reshape(-1) / 3.0)
            steer.append(st + 1)
            throttle.append(th)
    X = np.stack(frames)
    y_s = np.asarray(steer, dtype=np.int64)
    y_t = np.asarray(throttle, dtype=np.int64)
    with torch.no_grad():
        ps, pt = model(torch.from_numpy(X))
    pred_s = ps.argmax(1).numpy()
    pred_t = pt.argmax(1).numpy()
    n = len(y_s)

    steer_rows = {}
    for cls in (-1, 0, 1):
        mask = y_s == (cls + 1)
        acc = float((pred_s[mask] == y_s[mask]).mean()) if mask.any() else 0.0
        steer_rows[STEER_LABELS[cls]] = {
            "count": int(mask.sum()),
            "fraction": round(float(mask.mean()), 4),
            "accuracy": round(acc, 4),
        }
    throttle_rows = {}
    for cls in (0, 1):
        mask = y_t == cls
        acc = float((pred_t[mask] == y_t[mask]).mean()) if mask.any() else 0.0
        throttle_rows["brake" if cls == 0 else "accelerate"] = {
            "count": int(mask.sum()),
            "fraction": round(float(mask.mean()), 4),
            "accuracy": round(acc, 4),
        }

    dodge = y_s != 1  # expert steers nonzero
    joint = (pred_s == y_s) & (pred_t == y_t)
    return {
        "eval_frames": n,
        "steer_by_class": steer_rows,
        "throttle_by_class": throttle_rows,
        "dodge_frames": {
            "count": int(dodge.sum()),
            "fraction": round(float(dodge.mean()), 4),
            "joint_accuracy": round(float(joint[dodge].mean()), 4),
        },
        "straight_frames": {
            "count": int((~dodge).sum()),
            "fraction": round(float((~dodge).mean()), 4),
            "joint_accuracy": round(float(joint[~dodge].mean()), 4),
        },
    }


def closed_loop_divergence(model: CloneNet, scenarios) -> dict:
    """Part 2 -- where the clone's trajectory leaves the expert's."""
    first_div_steps = []
    disagree_total = 0
    disagree_steps = 0
    outcomes = {"completed": 0, "collision": 0, "offroad": 0, "timeout": 0}
    final_lat_dev = []
    clone = cloned_policy(model)
    for s in scenarios:
        car_e, car_c = Car(), Car()
        expert_e = make_expert(s)     # drives the expert car only
        expert_label = make_expert(s)  # labels clone states; never steps a car
        first_div = None
        for _ in range(MAX_STEPS):
            obs_e = render(s, car_e)
            act_e = expert_e(obs_e, car_e)
            obs_c = render(s, car_c)
            act_c = clone(obs_c, car_c)
            exp_on_clone = expert_label(obs_c, car_c)
            disagree_total += 1
            if exp_on_clone != act_c:
                disagree_steps += 1
            if first_div is None and abs(car_c.y - car_e.y) > DIVERGE_LAT_M:
                first_div = _
            car_e.step(*act_e)
            car_c.step(*act_c)
            end = _episode_end(s, car_c)
            if end:
                outcomes[end] += 1
                final_lat_dev.append(abs(car_c.y - car_e.y))
                if first_div is None:
                    first_div = MAX_STEPS
                break
        else:
            outcomes["timeout"] += 1
            final_lat_dev.append(abs(car_c.y - car_e.y))
            first_div = MAX_STEPS
        first_div_steps.append(first_div)

    n = len(scenarios)
    return {
        "scenarios": n,
        "outcomes": {k: round(v / n, 3) for k, v in outcomes.items()},
        "divergence": {
            "threshold_lat_m": DIVERGE_LAT_M,
            "mean_first_divergence_step": round(float(np.mean(first_div_steps)), 1),
            "median_first_divergence_step": float(np.median(first_div_steps)),
            "fraction_never_diverged": round(
                sum(1 for s_ in first_div_steps if s_ >= MAX_STEPS) / n, 3
            ),
        },
        "on_policy_expert_disagreement": {
            "steps_labeled": disagree_total,
            "fraction_expert_acts_differently": round(disagree_steps / disagree_total, 4),
        },
        "mean_final_lateral_deviation_m": round(float(np.mean(final_lat_dev)), 2),
    }


def main() -> None:
    t0 = time.time()
    scenarios = [sample_scenario(seed) for seed in EVAL_SEEDS]
    model = CloneNet()
    model.load_state_dict(torch.load(CLONE_DIR / "cloned_policy.pt", weights_only=True))
    model.eval()

    part1 = per_class_errors(model, scenarios)
    t1 = time.time()
    part2 = closed_loop_divergence(model, scenarios)
    t2 = time.time()

    RUNS.mkdir(parents=True, exist_ok=True)
    summary = {
        "command": "python error_origin.py",
        "hardware": {
            "machine": platform.machine(),
            "system": platform.system(),
            "python": platform.python_version(),
        },
        "cost_usd": 0.0,
        "part1_per_class_errors": part1,
        "part2_closed_loop_divergence": part2,
        "wall_clock_s": {
            "part1": round(t1 - t0, 2),
            "part2": round(t2 - t1, 2),
            "total": round(t2 - t0, 2),
        },
    }
    with (RUNS / "2026-08-08-error-origin.json").open("w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
