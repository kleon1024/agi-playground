"""Stage 02 -- the rule-based expert: lane keeping plus obstacle
avoidance, evaluated in the loop. This is the ceiling of what the behavior-
cloning stage can recover, because the learner's demonstrations come from
it, and the floor is the lane-only rule baseline (same controller, no
avoidance logic) that stage 04 also reports.

The expert sees the true state, not the render. Every step it re-plans a
lateral target offset: normally the lane center, but when an obstacle in
the current lane is reachable it picks the closest offset that clears every
obstacle in the decision window with margin, and it brakes only when no
lateral escape exists. It does not trust a stale "passed" flag -- an
obstacle keeps moving along the road, so a dodge is released only once the
obstacle's *current* position is well behind the car.

Usage:
    python expert.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

SIM_DIR = Path(__file__).resolve().parents[2] / "00-scenario-simulator" / "core"
sys.path.insert(0, str(SIM_DIR))
from driving_sim import (
    ROAD_HALF_WIDTH,
    STEER_RATE,
    sample_scenario,
    simulate,
)

RUNS = Path(__file__).resolve().parents[1] / "runs"

# Lateral offsets (relative to the lane center, in metres) the expert will
# consider. The road half-width is 2.0m, so +/-1.55 keeps a 0.45m shoulder.
CANDIDATE_OFFSETS = (0.0, 1.2, -1.2, 1.55, -1.55)
CLEARANCE_MARGIN = 0.45  # extra lateral metres beyond the collision radius
DODGE_RELEASE = 1.5  # obstacle must be this far behind before returning


def _obs_offset(scenario, ox: float, oy: float) -> float:
    return oy - scenario.lane_center(ox)


def _threats(scenario, car, window: float):
    """Obstacles inside the decision window, with their lateral offset."""
    out = []
    for ox, oy, r, vx in scenario.obstacles:
        dx = ox - car.x
        if dx < -DODGE_RELEASE or dx > window:
            continue
        out.append((dx, ox, oy, r, vx))
    return out


def _safe_offsets(scenario, car, threats) -> list[float]:
    """Offsets that clear every obstacle in `threats` with margin."""
    safe = []
    for off in CANDIDATE_OFFSETS:
        if abs(off) > ROAD_HALF_WIDTH - 0.35:
            continue
        if all(
            abs(off - _obs_offset(scenario, ox, oy)) >= r + CLEARANCE_MARGIN
            for _dx, ox, oy, r, _vx in threats
        ):
            safe.append(off)
    return safe


def lane_only_policy(scenario, obs, car, lookahead: float = 3.0):
    """No-learning floor: steer toward the lane center, always accelerate."""
    y_target = scenario.lane_center(car.x + lookahead)
    theta_d = _clip_heading((y_target - car.y) / max(lookahead, 1e-6))
    steer = max(-1, min(1, round((theta_d - car.theta) / STEER_RATE)))
    return steer, 1


def make_expert(scenario):
    dodge = {"off": 0.0}

    def policy(obs, car):
        window = max(10.0, car.v * 2.5)
        threats = _threats(scenario, car, window)
        cur_off = car.y - scenario.lane_center(car.x)

        if not threats:
            dodge["off"] = 0.0
            return _steer_to(scenario, car, 0.0, 3.0), 1

        # Trigger on the nearest obstacle the current offset does NOT clear:
        # waiting for it to become the nearest obstacle fires too late when a
        # passable obstacle at a different offset masks it until it is almost
        # alongside. Lane choice still re-plans sequentially, so obstacles
        # farther ahead never veto a dodge.
        nearest = min(threats, key=lambda t: t[0])
        conflict = None
        for dx, ox, oy, r, _vx in threats:
            if (abs(cur_off - _obs_offset(scenario, ox, oy)) < r + CLEARANCE_MARGIN
                    and (conflict is None or dx < conflict[0])):
                conflict = (dx, ox, oy, r)
        n_dx, n_ox, n_oy, n_r = (
            conflict if conflict is not None else (nearest[0], nearest[1], nearest[2], nearest[3])
        )
        n_gap = abs(cur_off - _obs_offset(scenario, n_ox, n_oy))

        # Speed governor: the discrete steering controller can only hold a
        # lateral offset precisely at low speed, so approach every obstacle
        # zone slowly and accelerate only in clear stretches. The obstacle
        # is static, so arriving slow never costs the maneuver.
        target_speed = 4.0
        if n_dx < 8.0:
            target_speed = 2.5

        if conflict is not None:
            # the nearest obstacle conflicts with the current offset: dodge.
            # Verify the dodge lane against obstacles up to 2m past the
            # nearest one; anything farther is re-planned as it gets closer.
            horizon = n_dx + 2.0
            near = [t for t in threats if t[0] < horizon]
            safe = _safe_offsets(scenario, car, near)
            if dodge["off"] in safe:
                target_off = dodge["off"]
            elif safe:
                target_off = min(safe, key=lambda o: abs(o - cur_off))
            else:
                # no lane clears the near group: keep the current offset and
                # creep past sequentially; the obstacles separate as the car
                # passes them one at a time
                target_off = cur_off
            if n_dx < 3.0 and n_gap < n_r + 0.55:
                target_speed = 1.2
        elif dodge["off"] != 0.0 and nearest[0] > -DODGE_RELEASE:
            # no conflict, but a dodge is still in flight and the obstacle
            # that triggered it has not yet fallen well behind: hold the
            # dodge offset instead of cutting back through the obstacle's
            # path. Returning to center on every "barely safe" step makes
            # the margin check flip-flop and turns a clean pass into a
            # collision.
            target_off = dodge["off"]
            throttle = 1
        else:
            # lane is clear: drive the center line
            target_off = 0.0
            target_speed = 6.0
        dodge["off"] = target_off
        throttle = 0 if car.v > target_speed + 0.15 else 1

        lookahead = 2.0 if abs(target_off) > 0.05 else 3.0
        return _steer_to(scenario, car, target_off, lookahead), throttle

    return policy


def _steer_to(scenario, car, offset: float, lookahead: float):
    y_target = scenario.lane_center(car.x + lookahead) + offset
    theta_d = _clip_heading((y_target - car.y) / max(lookahead, 1e-6))
    return max(-1, min(1, round((theta_d - car.theta) / STEER_RATE)))


def _clip_heading(v: float) -> float:
    return max(-0.6, min(0.6, v))


def _eval(scenarios, policy_factory):
    results = {"completed": 0, "collided": 0, "offroad": 0, "timeout": 0,
               "steps": [], "x": []}
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
        results["steps"].append(out.steps)
        results["x"].append(out.x_reached)
    n = len(scenarios)
    return {
        "scenarios": n,
        "completion_rate": round(results["completed"] / n, 3),
        "collision_rate": round(results["collided"] / n, 3),
        "offroad_rate": round(results["offroad"] / n, 3),
        "timeout_rate": round(results["timeout"] / n, 3),
        "mean_steps": round(sum(results["steps"]) / n, 1),
        "mean_x_reached": round(sum(results["x"]) / n, 2),
    }


def main() -> None:
    scenarios = [sample_scenario(seed) for seed in range(100, 150)]

    t0 = time.time()
    lane_only = _eval(scenarios, lambda s: lambda obs, car: lane_only_policy(s, obs, car))
    lane_only["wall_clock_s"] = round(time.time() - t0, 2)

    t0 = time.time()
    expert = _eval(scenarios, make_expert)
    expert["wall_clock_s"] = round(time.time() - t0, 2)

    RUNS.mkdir(parents=True, exist_ok=True)
    for name, summary in (("lane-only", lane_only), ("expert", expert)):
        with (RUNS / f"2026-08-07-{name}.json").open("w") as f:
            json.dump(summary, f, indent=2)
    print("lane-only:", json.dumps(lane_only, indent=2))
    print("expert:   ", json.dumps(expert, indent=2))


if __name__ == "__main__":
    main()
