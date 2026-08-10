"""Measure both of mission 06's required baselines -- random and greedy
one-step-lookahead -- over many independently sampled grids, and report
real success rates. This is the number stage 01's GRPO run has to beat, and
mission.yaml's guardrail against a starting policy too weak for GRPO to move
at all applies just as much to picking an environment: a task this easy
(near-100% for the heuristic) or this hard (near-0% for everything) would
leave no room for a training run to say anything.

Run:
    uv run python measure_baselines.py --trials 500
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from baselines import greedy_policy, random_policy
from gridworld import sample_grid


def evaluate(policy_name: str, size: int, num_walls: int, max_steps: int, trials: int, seed: int) -> dict:
    rng = random.Random(seed)
    successes = 0
    steps_on_success = []
    for _ in range(trials):
        grid = sample_grid(rng, size=size, num_walls=num_walls)
        if policy_name == "random":
            actions = random_policy(rng, max_steps)
        elif policy_name == "greedy":
            actions = greedy_policy(grid, max_steps)
        else:
            raise ValueError(policy_name)
        reached, steps = grid.run_episode(actions, max_steps)
        if reached:
            successes += 1
            steps_on_success.append(steps)
    return {
        "policy": policy_name,
        "trials": trials,
        "successes": successes,
        "success_rate": successes / trials,
        "mean_steps_on_success": sum(steps_on_success) / len(steps_on_success) if steps_on_success else None,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=5)
    ap.add_argument("--num-walls", type=int, default=4)
    ap.add_argument("--max-steps", type=int, default=12)
    ap.add_argument("--trials", type=int, default=500)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "runs" / "baselines.json")
    args = ap.parse_args()

    t0 = time.perf_counter()
    results = {
        "random": evaluate("random", args.size, args.num_walls, args.max_steps, args.trials, args.seed),
        "greedy": evaluate("greedy", args.size, args.num_walls, args.max_steps, args.trials, args.seed),
    }
    elapsed = time.perf_counter() - t0

    for name, r in results.items():
        print(
            f"{name:>7}: {r['successes']}/{r['trials']} = {r['success_rate']:.3f}  "
            f"mean_steps_on_success={r['mean_steps_on_success']}"
        )
    print(f"wall-clock: {elapsed:.2f}s")

    out = {
        "size": args.size,
        "num_walls": args.num_walls,
        "max_steps": args.max_steps,
        "trials": args.trials,
        "seed": args.seed,
        "wall_clock_s": elapsed,
        "results": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
