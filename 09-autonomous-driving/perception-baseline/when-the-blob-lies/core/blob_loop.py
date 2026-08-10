"""Detour 01-a -- what happens when a policy steers from blob estimates.

Stage 01 measures perception open-loop: the hand estimator's obstacle
distance MAE is 0.469m on expert frames, and the learned estimator fails at
obstacle distance entirely (6.526m). This script closes the loop: it feeds
the expert's own decision logic with blob beliefs built from the render --
the only thing a controller could build from pixels -- and rolls the result
out on the same 50 eval scenarios.

Part 1 (the blob estimator): connected components of obstacle-valued pixels
(v >= 2.0) in the 32x32 render. Distance is the nearest row, lateral is the
pixel centroid, radius is half the vertical extent. Measured against the
true nearest obstacle ahead on full expert rollouts.

Part 2 (the belief planner): the oracle expert re-targeted onto blob
beliefs per step, collision-checked against the true world. The oracle rate
is 0.92 completion / 0.08 collision; the belief planner's own rate is the
closed-loop price of stage 01's open-loop error.

Part 3 (the fix attempts): radius-margin bump, cached track, a cautious
speed governor, and a multi-blob belief -- four planner-side repairs a stack
might reach for, each measured to see whether it restores the oracle rate.

Part 4 (the forensics): per-collision classification for every episode the
belief planner loses -- how late the belief vanished, whether the planner
cut back across a just-passed obstacle, and whether a second threat sat in
the same decision window.

Usage:
    python blob_loop.py
"""

from __future__ import annotations

import json
import math
import platform
import sys
import time
from collections import deque
from pathlib import Path

SIM_DIR = Path(__file__).resolve().parents[3] / "00-scenario-simulator" / "core"
EXP_DIR = Path(__file__).resolve().parents[3] / "02-expert-policy" / "core"
sys.path.insert(0, str(SIM_DIR))
sys.path.insert(0, str(EXP_DIR))
import expert as expert_mod
from driving_sim import (
    GRID,
    M_PER_PIX,
    MAX_STEPS,
    PATCH,
    ROAD_HALF_WIDTH,
    TARGET_X,
    Car,
    render,
    sample_scenario,
    simulate,
)
from expert import make_expert

RUNS = Path(__file__).resolve().parents[1] / "runs"
EVAL_SEEDS = range(100, 150)
OBSTACLE_VALUE = 2.0


def blobs(grid) -> list[tuple[float, float, float]]:
    """Connected components of obstacle-valued pixels.

    Returns (distance, lateral, radius) per blob, distance-sorted, where
    distance is the nearest rendered row in metres ahead of the car, lateral
    is the mean lateral offset of the blob's pixels, and radius is half the
    blob's vertical extent in metres.
    """
    seen = [[False] * GRID for _ in range(GRID)]
    out = []
    for r0 in range(GRID):
        for c0 in range(GRID):
            if grid[r0][c0] < OBSTACLE_VALUE or seen[r0][c0]:
                continue
            queue = deque([(r0, c0)])
            seen[r0][c0] = True
            rows, cols = [], []
            while queue:
                r, c = queue.popleft()
                rows.append(r)
                cols.append(c)
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < GRID
                        and 0 <= cc < GRID
                        and not seen[rr][cc]
                        and grid[rr][cc] >= OBSTACLE_VALUE
                    ):
                        seen[rr][cc] = True
                        queue.append((rr, cc))
            min_row = min(rows)
            dist = PATCH * (1.0 - (min_row + 0.5) / GRID)
            lat = PATCH * (sum(cols) / len(cols) / GRID - 0.5 + 0.5 / GRID)
            radius = (max(rows) - min_row + 1) / 2.0 * M_PER_PIX
            out.append((dist, lat, radius))
    out.sort(key=lambda b: b[0])
    return out


def _true_nearest(scenario, car):
    """Nearest obstacle the render can show, in the car's frame."""
    cos_t, sin_t = math.cos(car.theta), math.sin(car.theta)
    best = None
    for ox, oy, _r, _vx in scenario.obstacles:
        dx, dy = ox - car.x, oy - car.y
        ahead = dx * cos_t + dy * sin_t
        lat = -dx * sin_t + dy * cos_t
        if ahead <= 0.0 or ahead > PATCH + 0.5:
            continue
        if best is None or ahead < best[0]:
            best = (ahead, lat)
    return best


def expert_rollouts(scenarios):
    """Full oracle episodes; every frame labelled with the true nearest
    obstacle ahead (None when nothing renderable is ahead)."""
    frames = []
    for s in scenarios:
        car = Car()
        policy = make_expert(s)
        for _ in range(MAX_STEPS):
            obs = render(s, car)
            steer, throttle = policy(obs, car)
            frames.append((obs, _true_nearest(s, car)))
            car.step(steer, throttle)
            if any(
                math.hypot(car.x - ox, car.y - oy) < r + 0.35
                for ox, oy, r, _ in s.obstacles
            ):
                break
            if abs(car.y - s.lane_center(car.x)) > ROAD_HALF_WIDTH:
                break
            if car.x >= TARGET_X:
                break
    return frames


def measure_estimator(frames) -> dict:
    """Blob estimates vs true nearest obstacle on visible frames."""
    total = len(frames)
    visible = 0
    blob_counts = {0: 0, 1: 0, 2: 0, "3+": 0}
    dist_err = {"0-2": [], "2-4": [], "4-6": [], "6-8": []}
    lat_err = {"0-2": [], "2-4": [], "4-6": [], "6-8": []}
    for obs, truth in frames:
        bs = blobs(obs)
        n = len(bs)
        if n == 0:
            blob_counts[0] += 1
        elif n == 1:
            blob_counts[1] += 1
        elif n == 2:
            blob_counts[2] += 1
        else:
            blob_counts["3+"] += 1
        if truth is None or not bs:
            continue
        visible += 1
        est_d, est_lat, _r = bs[0]
        t_d, t_lat = truth
        bucket = "0-2" if t_d < 2 else "2-4" if t_d < 4 else "4-6" if t_d < 6 else "6-8"
        dist_err[bucket].append(abs(est_d - t_d))
        lat_err[bucket].append(abs(est_lat - t_lat))

    def mae(vals):
        return round(sum(vals) / len(vals), 3) if vals else None

    dist_rows = {
        b: {"n": len(dist_err[b]), "mae_m": mae(dist_err[b])}
        for b in dist_err
    }
    lat_rows = {
        b: {"n": len(lat_err[b]), "mae_m": mae(lat_err[b])}
        for b in lat_err
    }
    all_dist = [e for b in dist_err.values() for e in b]
    all_lat = [e for b in lat_err.values() for e in b]
    return {
        "frames": total,
        "visible_frames": visible,
        "visible_fraction": round(visible / total, 4),
        "blob_count_distribution": blob_counts,
        "distance_mae_by_true_distance_m": dist_rows,
        "lateral_mae_by_true_distance_m": lat_rows,
        "distance_mae_overall_m": mae(all_dist),
        "lateral_mae_overall_m": mae(all_lat),
    }


class BeliefPlanner:
    """The oracle expert, re-targeted onto blob beliefs per step.

    The belief scenario's obstacle list is rewritten each step from the
    render, so the expert's decision logic (threat trigger, dodge selection,
    hold-until-passed, speed governor) runs unchanged -- only its input is
    now what a controller could actually see.
    """

    def __init__(self, scenario, radius_margin: float | None = None,
                 use_cache: bool = False, use_all_blobs: bool = False):
        self.scenario = scenario
        self.belief_scenario = sample_scenario(scenario.seed)
        self.belief_scenario.obstacles = []
        if radius_margin is not None:
            expert_mod.CLEARANCE_MARGIN = radius_margin
        self.expert = make_expert(self.belief_scenario)
        self.use_cache = use_cache
        self.use_all_blobs = use_all_blobs
        self.cache = None
        self.cache_age = 0
        self.belief = None

    def _belief_obstacles(self, obs, car):
        bs = blobs(obs)
        cos_t, sin_t = math.cos(car.theta), math.sin(car.theta)
        if bs:
            chosen = bs if self.use_all_blobs else bs[:1]
            d, lat, r = bs[0]
            self.belief = (d, lat, r)
            self.cache = (d, lat, r)
            self.cache_age = 0
            return [
                (
                    car.x + dd * cos_t - ll * sin_t,
                    car.y + dd * sin_t + ll * cos_t,
                    rr,
                    0.0,
                )
                for dd, ll, rr in chosen
            ]
        if self.use_cache and self.cache is not None and self.cache_age < 30:
            d, lat, r = self.cache
            d = max(0.0, d - car.v * 0.1)
            self.cache = (d, lat, r)
            self.cache_age += 1
            self.belief = (d, lat, r)
            if d < 0.5:
                self.cache = None
                return []
            return [
                (
                    car.x + d * cos_t - lat * sin_t,
                    car.y + d * sin_t + lat * cos_t,
                    r,
                    0.0,
                )
            ]
        self.cache = None
        self.belief = None
        return []

    def policy(self, obs, car):
        self.belief_scenario.obstacles = self._belief_obstacles(obs, car)
        return self.expert(obs, car)


def cautious_governor(planner: BeliefPlanner):
    """Brake whenever the current belief is within 4m."""

    def policy(obs, car):
        steer, throttle = planner.policy(obs, car)
        if planner.belief is not None and planner.belief[0] < 4.0:
            throttle = 0
        return steer, throttle

    return policy


def forensics(scenarios) -> dict:
    """Trace every episode the single-blob planner loses.

    For each collision episode, record the last 12 steps: car state, how many
    blobs were visible, the nearest blob's estimate (distance, lateral,
    radius, and the world lane offset it implies), and the true obstacles in
    the decision window. The association-flip signal fires when the nearest
    blob's car-frame lateral jumps by more than 1m between consecutive
    visible steps -- the belief re-attaching to a different obstacle.
    """
    rows = []
    for s in scenarios:
        planner = BeliefPlanner(s)
        car = Car()
        log = []
        collision_obs = None
        for _ in range(MAX_STEPS):
            obs = render(s, car)
            steer, throttle = planner.policy(obs, car)
            cur_off = car.y - s.lane_center(car.x)
            bs = blobs(obs)
            nearest = None
            if bs:
                d, lat, r = bs[0]
                ct, st = math.cos(car.theta), math.sin(car.theta)
                wx = car.x + d * ct - lat * st
                wy = car.y + d * st + lat * ct
                nearest = {
                    "d": round(d, 2),
                    "lat": round(lat, 2),
                    "r": round(r, 2),
                    "world_off": round(wy - s.lane_center(wx), 2),
                }
            win = [
                {
                    "dx": round(ox - car.x, 2),
                    "off": round(oy - s.lane_center(ox), 2),
                }
                for ox, oy, _r, _ in s.obstacles
                if -1.5 < (ox - car.x) <= 12.0
            ]
            log.append(
                {"x": round(car.x, 2), "v": round(car.v, 2),
                 "cur_off": round(cur_off, 2), "n_blobs": len(bs),
                 "nearest": nearest, "win": win}
            )
            car.step(steer, throttle)
            hit = None
            for ox, oy, r, _ in s.obstacles:
                if math.hypot(car.x - ox, car.y - oy) < r + 0.35:
                    hit = (ox, oy, r)
            if hit is not None:
                collision_obs = (
                    round(hit[0] - car.x, 2),
                    round(hit[1] - s.lane_center(hit[0]), 2),
                    round(hit[2], 2),
                )
                break
            if abs(car.y - s.lane_center(car.x)) > ROAD_HALF_WIDTH:
                break
            if car.x >= TARGET_X:
                break
        if collision_obs is None:
            continue
        tail = log[-12:]
        flip = False
        prev_lat = None
        for e in log[-15:]:
            if e["nearest"] is None:
                prev_lat = None
                continue
            if prev_lat is not None and abs(e["nearest"]["lat"] - prev_lat) > 1.0:
                flip = True
            prev_lat = e["nearest"]["lat"]
        last_visible = next(
            (e["nearest"] for e in reversed(log) if e["nearest"] is not None),
            None,
        )
        rows.append(
            {
                "seed": s.seed,
                "collision_obstacle_dx_m": collision_obs[0],
                "collision_obstacle_offset_m": collision_obs[1],
                "collision_obstacle_radius_m": collision_obs[2],
                "car_offset_at_collision_m": round(log[-1]["cur_off"], 2),
                "speed_at_collision_mps": round(log[-1]["v"], 2),
                "last_frame_blobs": log[-1]["n_blobs"],
                "association_flip_last_15": flip,
                "last_visible_belief_world_off_m": (
                    last_visible["world_off"] if last_visible else None
                ),
                "obstacles_in_window_at_collision": log[-1]["win"],
                "last_12_steps": tail,
            }
        )
    return {"collision_episodes": rows}


def _eval(policy_factory, scenarios) -> dict:
    results = {"completed": 0, "collided": 0, "offroad": 0, "timeout": 0,
               "steps": [], "fail_seeds": []}
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
        if not out.completed:
            results["fail_seeds"].append(s.seed)
    n = len(scenarios)
    return {
        "scenarios": n,
        "completion_rate": round(results["completed"] / n, 3),
        "collision_rate": round(results["collided"] / n, 3),
        "offroad_rate": round(results["offroad"] / n, 3),
        "timeout_rate": round(results["timeout"] / n, 3),
        "mean_steps": round(sum(results["steps"]) / n, 1),
        "fail_seeds": results["fail_seeds"],
    }


def main() -> None:
    t0 = time.time()
    scenarios = [sample_scenario(seed) for seed in EVAL_SEEDS]

    # Part 1: blob estimator against the oracle rollouts.
    frames = expert_rollouts(scenarios)
    estimator = measure_estimator(frames)

    # Part 2: the belief planner in the loop.
    belief = _eval(lambda s: BeliefPlanner(s).policy, scenarios)

    # Part 3: the planner-side repairs. The margin bump patches the expert
    # module's global, so snapshot and restore it around the run.
    original_margin = expert_mod.CLEARANCE_MARGIN
    margin_bump = _eval(
        lambda s: BeliefPlanner(s, radius_margin=0.68).policy, scenarios
    )
    expert_mod.CLEARANCE_MARGIN = original_margin
    cached = _eval(
        lambda s: BeliefPlanner(s, use_cache=True).policy, scenarios
    )
    cautious = _eval(
        lambda s: cautious_governor(BeliefPlanner(s)), scenarios
    )
    all_blobs = _eval(
        lambda s: BeliefPlanner(s, use_all_blobs=True).policy, scenarios
    )

    # Part 4: per-collision forensics of the single-blob planner.
    detail = forensics(scenarios)

    result = {
        "command": "python blob_loop.py",
        "hardware": {
            "machine": platform.machine(),
            "system": platform.system(),
            "python": platform.python_version(),
        },
        "cost_usd": 0.0,
        "oracle_expert_from_stage_02": {"completion_rate": 0.92, "collision_rate": 0.08},
        "part1_blob_estimator": estimator,
        "part2_belief_planner": belief,
        "part3_repairs": {
            "radius_margin_0_68": margin_bump,
            "cached_track": cached,
            "cautious_governor": cautious,
            "all_blobs": all_blobs,
        },
        "part4_collision_forensics": detail,
        "wall_clock_s": round(time.time() - t0, 2),
    }
    RUNS.mkdir(parents=True, exist_ok=True)
    with (RUNS / "2026-08-08-blob-loop.json").open("w") as f:
        json.dump(result, f, indent=2)

    print("part1 blob estimator:")
    print(json.dumps(estimator, indent=2))
    print("part2 belief planner:", json.dumps(belief, indent=2))
    print("part3 repairs:")
    for name, row in (
        ("radius_margin_0_68", margin_bump),
        ("cached_track", cached),
        ("cautious_governor", cautious),
        ("all_blobs", all_blobs),
    ):
        print(f"  {name}: comp {row['completion_rate']} "
              f"coll {row['collision_rate']}")
    print("part4 forensics:")
    for row in detail["collision_episodes"]:
        print(" ", row)
    print("wall_clock_s:", result["wall_clock_s"])


if __name__ == "__main__":
    main()
