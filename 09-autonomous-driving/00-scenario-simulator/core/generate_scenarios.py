"""Stage 00 -- generate the train/eval scenario split and render a grid of
sample frames, proving the split is disjoint by seed and the render carries
real road/obstacle signal.

Usage:
    python generate_scenarios.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from driving_sim import GRID, render, sample_scenario

RUNS = Path(__file__).resolve().parents[1] / "runs"


def main() -> None:
    t0 = time.time()
    train = [sample_scenario(seed) for seed in range(100)]
    eval_s = [sample_scenario(seed) for seed in range(100, 150)]
    wall = time.time() - t0

    # disjoint by construction (seed ranges), checked explicitly
    train_seeds = {s.seed for s in train}
    eval_seeds = {s.seed for s in eval_s}
    assert not (train_seeds & eval_seeds), "train/eval seed overlap"

    # obstacle density + render signal stats over the eval split
    n_obs = [len(s.obstacles) for s in eval_s]
    road_px, obs_px = [], []
    from driving_sim import Car
    for s in eval_s[:20]:
        grid = render(s, Car())
        flat = [v for row in grid for v in row]
        road_px.append(sum(1 for v in flat if v > 0.0 and v < 2.0))
        obs_px.append(sum(1 for v in flat if v >= 2.0))

    RUNS.mkdir(parents=True, exist_ok=True)
    summary = {
        "train_scenarios": len(train),
        "eval_scenarios": len(eval_s),
        "train_seed_range": [0, 99],
        "eval_seed_range": [100, 149],
        "eval_obstacle_min": min(n_obs),
        "eval_obstacle_max": max(n_obs),
        "eval_render_road_px_mean": round(sum(road_px) / len(road_px), 1),
        "eval_render_obs_px_mean": round(sum(obs_px) / len(obs_px), 1),
        "wall_clock_s": round(wall, 3),
        "grid": GRID,
        "patch_m": 8.0,
    }
    with (RUNS / "2026-08-07-scenario-generation.json").open("w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

