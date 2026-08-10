"""Random and scripted-heuristic baselines for MiniGrid, restated per
`mission.yaml`'s note that the heuristic baseline is declared concretely in
this stage's own README rather than in the contract itself.

Heuristic: wall-following (if the cell directly ahead is open, move
forward; otherwise turn right) -- a real, general navigation strategy, not
one that hardcodes this room's specific goal location.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import gymnasium as gym
import minigrid  # noqa: F401

FORWARD, TURN_LEFT, TURN_RIGHT = 2, 0, 1


def front_is_open(obs: dict) -> bool:
    """MiniGrid's 7x7 observation is agent-relative: row 3 (0-indexed) is
    the agent's own row, column 6 is one cell directly in front of it, per
    MiniGrid's fixed egocentric view convention (agent at (3, 6), facing
    toward increasing... the object one step ahead along the agent's
    forward axis sits at column 5 in this view, one column closer than the
    edge). Object id 1 (empty) or 8 (goal) is open; 2 (wall) is not."""
    obj_ahead = obs["image"][3, 5, 0]
    return obj_ahead in (1, 8)


def run_random(env: gym.Env, trials: int, max_steps: int, seed: int) -> dict:
    rng = random.Random(seed)
    successes = 0
    for i in range(trials):
        _obs, _info = env.reset(seed=seed + i)
        reached = False
        for _ in range(max_steps):
            action = rng.choice([FORWARD, TURN_LEFT, TURN_RIGHT])
            _obs, reward, terminated, truncated, _info = env.step(action)
            if terminated:
                reached = reward > 0
                break
            if truncated:
                break
        successes += int(reached)
    return {"trials": trials, "successes": successes, "success_rate": successes / trials}


def run_wall_follow(env: gym.Env, trials: int, max_steps: int, seed: int) -> dict:
    successes = 0
    for i in range(trials):
        obs, _info = env.reset(seed=seed + i)
        reached = False
        for _ in range(max_steps):
            action = FORWARD if front_is_open(obs) else TURN_RIGHT
            obs, reward, terminated, truncated, _info = env.step(action)
            if terminated:
                reached = reward > 0
                break
            if truncated:
                break
        successes += int(reached)
    return {"trials": trials, "successes": successes, "success_rate": successes / trials}


def main() -> None:
    env = gym.make("MiniGrid-Empty-6x6-v0", max_steps=10)
    result = {
        "random": run_random(env, trials=500, max_steps=10, seed=1_000_000),
        "wall_follow": run_wall_follow(env, trials=500, max_steps=10, seed=1_000_000),
    }
    env.close()
    print(json.dumps(result, indent=2))
    out_path = Path(__file__).resolve().parent.parent / "runs" / "minigrid-baselines.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
